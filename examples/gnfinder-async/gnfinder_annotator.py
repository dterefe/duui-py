from __future__ import annotations
import json
import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from collections.abc import AsyncIterator
from pathlib import Path
from time import time
from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import bad_gateway, timeout, unavailable
from duui_py.logging.core import get_configured_event_logger
from duui_py.telemetry import telemetry
from duui_py.models import (
    AnnotatorConfig, AnnotatorDescriptor, AnnotatorMeta,
    Domain, DomainSpec, DuuiResult, IODescriptor, V1RequestEnvelope,
)
from duui_py.models.uima import sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.biofid.gnfinder.types import (
    GNFinderTaxon, VerifiedTaxon,
)

DEFAULT_GNFINDER_BINARY = "gnfinder"


@lru_cache(maxsize=8)
def _resolve_binary(parameter_value: str | None) -> str | None:
    for candidate in (
        parameter_value,
        shutil.which("gnfinder"),
        DEFAULT_GNFINDER_BINARY,
    ):
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None
# ---------------------------------------------------------------------------
# Shared helpers (exported for gnfinder_rest_annotator.py)
# ---------------------------------------------------------------------------
def _to_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_int(value: object | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: object | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _name_to_taxon(name: dict[str, object], *, verify: bool) -> GNFinderTaxon:
    """Build a GNFinderTaxon or VerifiedTaxon from a single gnfinder name record."""
    begin = _to_int(name.get("start"))

    begin = _to_int(name.get("start"))
    end = _to_int(name.get("end"))
    if begin is None or end is None:
        bad_gateway("GNFinder name record is missing offsets", record=name)
    verification = name.get("verification")
    best_result: dict[str, object] | None = None
    if verify and isinstance(verification, dict) and isinstance(verification.get("bestResult"), dict):
        best_result = verification["bestResult"]
    if best_result is None:
        return GNFinderTaxon.model_construct(
            begin=begin, end=end,
            value=str(name.get("name") or name.get("verbatim") or ""),
            cardinality=_to_int(name.get("cardinality")),
            oddsLog10=_to_float(name.get("oddsLog10")),
        )
    current_name = best_result.get("currentName")
    outlink = best_result.get("outlink")
    return VerifiedTaxon.model_construct(
        begin=begin, end=end,
        value=str(current_name or name.get("name") or name.get("verbatim") or ""),
        identifier=str(outlink) if outlink is not None else None,
        cardinality=_to_int(name.get("cardinality")),
        oddsLog10=_to_float(name.get("oddsLog10")),
        currentName=str(current_name) if current_name is not None else None,
        dataSourceId=_to_int(best_result.get("dataSourceId")),
        editDistance=_to_int(best_result.get("editDistance")),
        globalId=str(best_result.get("globalId")) if best_result.get("globalId") is not None else None,
        localId=str(best_result.get("localId")) if best_result.get("localId") is not None else None,
        matchedCanonicalFull=str(best_result.get("matchedCanonicalFull")) if best_result.get("matchedCanonicalFull") is not None else None,
        matchedCanonicalSimple=str(best_result.get("matchedCanonicalSimple")) if best_result.get("matchedCanonicalSimple") is not None else None,
        matchedName=str(best_result.get("matchedName")) if best_result.get("matchedName") is not None else None,
        outlink=str(outlink) if outlink is not None else None,
        recordId=str(best_result.get("recordId")) if best_result.get("recordId") is not None else None,
        sortScore=_to_float(best_result.get("sortScore")),
    )


class GNFinderAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"example": "duui-gnfinder migration"}),
        descriptor=AnnotatorDescriptor(
            name="gnfinder-msgpack-lua",
            version="1.0.0",
            input=IODescriptor(
                text=DomainSpec(default=Domain(mimeType="text/plain; charset=utf-8", languages=["x-unspecified"])),
            ),
            output=IODescriptor(
                types={"Taxon": [
                    "org.texttechnologylab.annotation.biofid.gnfinder.Taxon",
                    "org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon",
                ]},
                text=DomainSpec(default=Domain(mimeType="text/plain; charset=utf-8", languages=["x-unspecified"])),
            ),
        ),
        typesystem_xml_path="TypeSystemGNFinder.xml",
        parameters_schema={
            "lang": {"type": "string", "default": "detect", "description": "Language hint for name detection."},
            "verify": {"type": "boolean", "default": True, "description": "Enable GNFinder name verification."},
            "gnfinder_binary": {"type": "string", "default": DEFAULT_GNFINDER_BINARY, "description": "Path to GNFinder executable."},
            "timeout_seconds": {"type": "number", "default": 120, "description": "Process timeout per invocation."},
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        logger = get_configured_event_logger()
        started = time()
        text = sofa_text_value(doc.sofa) or ""

        def _bool(val: object, default: bool = False) -> bool:
            if val is None:
                return default
            if isinstance(val, bool):
                return val
            return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}

        lang = str(doc.parameters.get("lang") or "detect")
        verify = _bool(doc.parameters.get("verify"), True)
        timeout_seconds = float(doc.parameters.get("timeout_seconds") or 120)
        binary = _resolve_binary(str(doc.parameters.get("gnfinder_binary") or ""))

        if logger is not None:
            await logger.info(
                f"GNFinder processing: text_length={len(text)} lang={lang} "
                f"verify={verify} timeout={timeout_seconds}"
            )

        if binary is None:
            if logger is not None:
                await logger.error("GNFinder binary not available")
            unavailable("GNFinder binary is not available.", configured_binary=DEFAULT_GNFINDER_BINARY)

        await telemetry.info(
            "GNFinder processing started",
            text_length=len(text), lang=lang, verify=verify, binary=binary,
        )

        # -- invoke gnfinder CLI -------------------------------------------------
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(text)
            input_path = handle.name
        try:
            command = [binary, input_path, "-f", "compact"]
            if verify:
                command.append("-v")
            if lang and lang != "detect":
                command.extend(["-l", lang])
            completed = subprocess.run(
                command, capture_output=True, check=False,
                encoding="utf-8", timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            if logger is not None:
                await logger.error(f"GNFinder timed out after {timeout_seconds}s")
            timeout("GNFinder process timed out", timeout_seconds=timeout_seconds, binary=binary)
        finally:
            Path(input_path).unlink(missing_ok=True)

        if completed.returncode != 0:
            if logger is not None:
                await logger.error(f"gnfinder CLI failed: rc={completed.returncode} stderr={completed.stderr.strip()}")
            bad_gateway("GNFinder process failed", returncode=completed.returncode, stderr=completed.stderr.strip())

        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            bad_gateway("GNFinder returned invalid JSON", error=str(exc))
        if not isinstance(result, dict):
            bad_gateway("GNFinder returned unexpected JSON root", json_type=type(result).__name__)

        # -- parse results -------------------------------------------------------
        names = result.get("names", [])
        if not isinstance(names, list):
            bad_gateway("GNFinder result has invalid names field", field_type=type(names).__name__)

        taxons: list[GNFinderTaxon] = []
        for name in names:
            if isinstance(name, dict):
                taxons.append(_name_to_taxon(name, verify=verify))

        if logger is not None:
            await logger.info(f"GNFinder: {len(taxons)} taxons from {len(names)} names (verify={verify})")

        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count("gnfinder_taxon_matches", len(taxons), lang=lang, verify=str(verify).lower())
        await telemetry.timing("gnfinder_processing_ms", elapsed_ms)
        await telemetry.info("GNFinder processing completed", matches=len(taxons), elapsed_ms=elapsed_ms, verify=verify)

        yield DuuiResult.model_construct(
            annotations=taxons, feature_structures=[], meta=None,
            modification_meta=None, errors=[], sofa=None,
        )


app = create_app(GNFinderAnnotator, request_adapter=AsyncChunkedRequestAdapter())
