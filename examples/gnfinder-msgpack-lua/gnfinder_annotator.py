from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import bad_gateway, timeout, unavailable
from duui_py.logging import get_event_logger_or_none
from duui_py.metrics import metrics
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    AnnotatorMetaData,
    DocumentModification,
    Domain,
    DomainSpec,
    IODescriptor,
    V1RequestEnvelope,
)
from duui_py.models.uima import sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.biofid.gnfinder.types import (
    GNFinderMetaData,
    GNFinderTaxon,
    VerifiedTaxon,
)

DEFAULT_GNFINDER_BINARY = "gnfinder"


def _resolve_binary(parameter_value: object | None = None) -> str | None:
    candidates = [
        str(parameter_value) if parameter_value else None,
        os.getenv("GNFINDER_BINARY"),
        shutil.which("gnfinder"),
        DEFAULT_GNFINDER_BINARY,
        "/home/stud_homes/s0424382/projects/ttlab/duui/TTLab-UIMA/GNFinder/gnfinder",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _run_gnfinder(
    *,
    binary: str,
    text: str,
    verify: bool,
    lang: str,
    timeout_seconds: float,
) -> dict[str, object]:
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
            command,
            capture_output=True,
            check=False,
            encoding="utf-8",
            timeout=timeout_seconds,
        )
    finally:
        Path(input_path).unlink(missing_ok=True)

    if completed.returncode != 0:
        bad_gateway(
            "GNFinder process failed",
            returncode=completed.returncode,
            stderr=completed.stderr.strip(),
        )

    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        bad_gateway("GNFinder returned invalid JSON", error=str(exc))

    if not isinstance(parsed, dict):
        bad_gateway("GNFinder returned an unexpected JSON root", json_type=type(parsed).__name__)
    return parsed


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
    begin = _to_int(name.get("start"))
    end = _to_int(name.get("end"))
    if begin is None or end is None:
        bad_gateway("GNFinder name record is missing offsets", record=name)

    verification = name.get("verification")
    best_result: dict[str, object] | None = None
    if verify and isinstance(verification, dict) and isinstance(verification.get("bestResult"), dict):
        best_result = verification["bestResult"]

    if best_result is None:
        return GNFinderTaxon(
            begin=begin,
            end=end,
            value=str(name.get("name") or name.get("verbatim") or ""),
            cardinality=_to_int(name.get("cardinality")),
            oddsLog10=_to_float(name.get("oddsLog10")),
        )

    current_name = best_result.get("currentName")
    outlink = best_result.get("outlink")
    return VerifiedTaxon(
        begin=begin,
        end=end,
        value=str(current_name or name.get("name") or name.get("verbatim") or ""),
        identifier=str(outlink) if outlink is not None else None,
        cardinality=_to_int(name.get("cardinality")),
        oddsLog10=_to_float(name.get("oddsLog10")),
        currentName=str(current_name) if current_name is not None else None,
        dataSourceId=_to_int(best_result.get("dataSourceId")),
        editDistance=_to_int(best_result.get("editDistance")),
        globalId=str(best_result.get("globalId")) if best_result.get("globalId") is not None else None,
        localId=str(best_result.get("localId")) if best_result.get("localId") is not None else None,
        matchedCanonicalFull=(
            str(best_result.get("matchedCanonicalFull"))
            if best_result.get("matchedCanonicalFull") is not None
            else None
        ),
        matchedCanonicalSimple=(
            str(best_result.get("matchedCanonicalSimple"))
            if best_result.get("matchedCanonicalSimple") is not None
            else None
        ),
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
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                )
            ),
            output=IODescriptor(
                types={
                    "Taxon": [
                        "org.texttechnologylab.annotation.biofid.gnfinder.Taxon",
                        "org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon",
                    ]
                },
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemGNFinder.xml",
        parameters_schema={
            "lang": {
                "type": "string",
                "default": "detect",
                "description": "Language hint for name detection.",
            },
            "verify": {
                "type": "boolean",
                "default": True,
                "description": "Keep parity with GNFinder verify parameter.",
            },
            "gnfinder_binary": {
                "type": "string",
                "default": DEFAULT_GNFINDER_BINARY,
                "description": "Path to the GNFinder executable.",
            },
            "timeout_seconds": {
                "type": "number",
                "default": 120,
                "description": "Process timeout for one GNFinder invocation.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        lang = str(doc.parameters.get("lang") or "detect")
        verify = bool(doc.parameters.get("verify", True))
        timeout_seconds = float(doc.parameters.get("timeout_seconds") or 120)
        binary = _resolve_binary(doc.parameters.get("gnfinder_binary"))
        logger = get_event_logger_or_none()

        if binary is None:
            unavailable(
                "GNFinder binary is not available",
                configured_binary=str(doc.parameters.get("gnfinder_binary") or os.getenv("GNFINDER_BINARY") or DEFAULT_GNFINDER_BINARY),
            )
        assert binary is not None

        if logger is not None:
            await logger.info(
                "GNFinder processing started",
                extra={"text_length": len(text), "lang": lang, "verify": verify, "binary": binary},
            )

        try:
            result = await asyncio.to_thread(
                _run_gnfinder,
                binary=binary,
                text=text,
                verify=verify,
                lang=lang,
                timeout_seconds=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            timeout("GNFinder process timed out", timeout_seconds=timeout_seconds, binary=binary)

        matches = 0
        names = result.get("names", [])
        if not isinstance(names, list):
            bad_gateway("GNFinder result has invalid names field", field_type=type(names).__name__)

        for name in names:
            if not isinstance(name, dict):
                continue
            matches += 1
            yield _name_to_taxon(name, verify=verify)

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("gnfinder_taxon_matches", matches, lang=lang, verify=str(verify).lower())
        await metrics.timing("gnfinder_processing_ms", elapsed_ms)

        metadata = result.get("metadata", {})
        if isinstance(metadata, dict):
            yield GNFinderMetaData(
                date=str(metadata.get("date")) if metadata.get("date") is not None else None,
                language=str(metadata.get("language")) if metadata.get("language") is not None else None,
                version=str(metadata.get("gnfinderVersion")) if metadata.get("gnfinderVersion") is not None else None,
            )

        if logger is not None:
            await logger.info(
                "GNFinder processing completed",
                extra={"matches": matches, "elapsed_ms": elapsed_ms, "verify": verify},
            )

        yield AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName="gnfinder",
                modelVersion=(
                    str(metadata.get("gnfinderVersion"))
                    if isinstance(metadata, dict) and metadata.get("gnfinderVersion") is not None
                    else None
                ),
        )
        yield DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} GNFinder extraction",
        )


app = create_app(GNFinderAnnotator, request_adapter=AsyncChunkedRequestAdapter())
