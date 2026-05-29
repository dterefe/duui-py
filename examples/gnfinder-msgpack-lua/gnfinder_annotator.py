from __future__ import annotations
import asyncio
import json
import logging
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
from duui_py.telemetry import telemetry
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    AnnotatorMetaData,
    DocumentModification,
    Domain,
    DomainSpec,
    DuuiResult,
    IODescriptor,
    V1RequestEnvelope,
)
from duui_py.models.uima import sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.biofid.gnfinder.types import (
    GNFinderTaxon,
    VerifiedTaxon,
)

logger = logging.getLogger(__name__)

DEFAULT_GNFINDER_BINARY = "gnfinder"
LEGACY_GNFINDER_BINARY = (
    "/home/stud_homes/s0424382/projects/ttlab/duui/duui-uima/"
    "duui-GNFinder/gnfinder"
)


def _resolve_binary(parameter_value: object | None = None) -> str | None:
    configured = str(parameter_value) if parameter_value else None
    return _resolve_binary_cached(configured)


@lru_cache(maxsize=32)
def _resolve_binary_cached(parameter_value: str | None) -> str | None:
    candidates = [
        parameter_value,
        shutil.which("gnfinder"),
        DEFAULT_GNFINDER_BINARY,
        LEGACY_GNFINDER_BINARY,
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
    utf8_input: bool,
    no_bayes: bool,
    adjust_odds: bool,
    ambiguous_uninomials: bool,
    all_matches: bool,
    unique_names: bool,
    sources: str | None,
    words_around: int | None,
) -> dict[str, object]:
    logger.debug(
        "Running gnfinder CLI: binary=%s text_length=%d verify=%s lang=%s timeout=%s",
        binary, len(text), verify, lang, timeout_seconds,
    )
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(text)
        input_path = handle.name
    try:
        command = [binary, input_path, "-f", "compact"]
        if utf8_input:
            command.append("-U")
        if verify:
            command.append("-v")
        if lang and lang != "detect":
            command.extend(["-l", lang])
        if no_bayes:
            command.append("-n")
        if adjust_odds:
            command.append("-a")
        if ambiguous_uninomials:
            command.append("-A")
        if all_matches:
            command.append("-M")
        if unique_names:
            command.append("-u")
        if sources:
            command.extend(["-s", sources])
        if words_around is not None:
            command.extend(["-w", str(words_around)])
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
        logger.error(
            "gnfinder CLI failed: returncode=%d stderr=%s",
            completed.returncode,
            completed.stderr.strip(),
        )
        bad_gateway(
            "GNFinder process failed",
            returncode=completed.returncode,
            stderr=completed.stderr.strip(),
        )
    try:
        parsed = json.loads(completed.stdout)
        logger.debug("gnfinder CLI returned valid JSON")
    except json.JSONDecodeError as exc:
        logger.error("gnfinder CLI returned invalid JSON: %s", exc)
        bad_gateway("GNFinder returned invalid JSON", error=str(exc))
    if not isinstance(parsed, dict):
        bad_gateway(
            "GNFinder returned an unexpected JSON root", json_type=type(parsed).__name__
        )
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


def _to_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _name_to_taxon(name: dict[str, object], *, verify: bool) -> GNFinderTaxon:
    begin = _to_int(name.get("start"))
    end = _to_int(name.get("end"))
    if begin is None or end is None:
        bad_gateway("GNFinder name record is missing offsets", record=name)
    verification = name.get("verification")
    best_result: dict[str, object] | None = None
    if (
        verify
        and isinstance(verification, dict)
        and isinstance(verification.get("bestResult"), dict)
    ):
        best_result = verification["bestResult"]
    if best_result is None:
        return GNFinderTaxon.model_construct(
            begin=begin,
            end=end,
            value=str(name.get("name") or name.get("verbatim") or ""),
            cardinality=_to_int(name.get("cardinality")),
            oddsLog10=_to_float(name.get("oddsLog10")),
        )
    current_name = best_result.get("currentName")
    outlink = best_result.get("outlink")
    return VerifiedTaxon.model_construct(
        begin=begin,
        end=end,
        value=str(current_name or name.get("name") or name.get("verbatim") or ""),
        identifier=str(outlink) if outlink is not None else None,
        cardinality=_to_int(name.get("cardinality")),
        oddsLog10=_to_float(name.get("oddsLog10")),
        currentName=str(current_name) if current_name is not None else None,
        dataSourceId=_to_int(best_result.get("dataSourceId")),
        editDistance=_to_int(best_result.get("editDistance")),
        globalId=(
            str(best_result.get("globalId"))
            if best_result.get("globalId") is not None
            else None
        ),
        localId=(
            str(best_result.get("localId"))
            if best_result.get("localId") is not None
            else None
        ),
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
        matchedName=(
            str(best_result.get("matchedName"))
            if best_result.get("matchedName") is not None
            else None
        ),
        outlink=str(outlink) if outlink is not None else None,
        recordId=(
            str(best_result.get("recordId"))
            if best_result.get("recordId") is not None
            else None
        ),
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
            "utf8_input": {
                "type": "boolean",
                "default": True,
                "description": "Use GNFinder -U for plain UTF-8 text and avoid Tika conversion.",
            },
            "no_bayes": {
                "type": "boolean",
                "default": False,
                "description": "Use GNFinder -n to disable Bayes algorithms.",
            },
            "adjust_odds": {
                "type": "boolean",
                "default": False,
                "description": "Use GNFinder -a to adjust Bayes odds by found-name density.",
            },
            "ambiguous_uninomials": {
                "type": "boolean",
                "default": False,
                "description": "Use GNFinder -A to preserve uninomials that are also common words.",
            },
            "all_matches": {
                "type": "boolean",
                "default": False,
                "description": "Use GNFinder -M to return all verification matches.",
            },
            "unique_names": {
                "type": "boolean",
                "default": False,
                "description": "Use GNFinder -u to return unique names.",
            },
            "sources": {
                "type": "string",
                "description": "Use GNFinder -s to restrict verification data-source ids, e.g. '4,11'.",
            },
            "words_around": {
                "type": "integer",
                "description": "Use GNFinder -w to include surrounding words.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        lang = str(doc.parameters.get("lang") or "detect")
        verify = _to_bool(doc.parameters.get("verify"), True)
        timeout_seconds = float(doc.parameters.get("timeout_seconds") or 120)
        utf8_input = _to_bool(doc.parameters.get("utf8_input"), True)
        no_bayes = _to_bool(doc.parameters.get("no_bayes"))
        adjust_odds = _to_bool(doc.parameters.get("adjust_odds"))
        ambiguous_uninomials = _to_bool(doc.parameters.get("ambiguous_uninomials"))
        all_matches = _to_bool(doc.parameters.get("all_matches"))
        unique_names = _to_bool(doc.parameters.get("unique_names"))
        sources = doc.parameters.get("sources")
        sources = str(sources) if sources is not None and str(sources).strip() else None
        words_around = _to_int(doc.parameters.get("words_around"))
        logger.info(
            "GNFinder processing started: text_length=%d lang=%s verify=%s utf8=%s timeout=%s",
            len(text), lang, verify, utf8_input, timeout_seconds,
        )
        binary = _resolve_binary(doc.parameters.get("gnfinder_binary"))
        if binary is None:
            logger.error(
                "GNFinder binary not available: configured=%s",
                doc.parameters.get("gnfinder_binary") or DEFAULT_GNFINDER_BINARY,
            )
            unavailable(
                "GNFinder binary is not available",
                configured_binary=str(
                    doc.parameters.get("gnfinder_binary")
                    or DEFAULT_GNFINDER_BINARY
                ),
            )
        assert binary is not None
        logger.debug("GNFinder resolved binary: %s", binary)
        await telemetry.info(
            "GNFinder processing started",
            text_length=len(text),
            lang=lang,
            verify=verify,
            binary=binary,
            utf8_input=utf8_input,
            no_bayes=no_bayes,
            adjust_odds=adjust_odds,
            ambiguous_uninomials=ambiguous_uninomials,
            all_matches=all_matches,
            unique_names=unique_names,
            sources=sources,
            words_around=words_around,
        )
        try:
            result = await asyncio.to_thread(
                _run_gnfinder,
                binary=binary,
                text=text,
                verify=verify,
                lang=lang,
                timeout_seconds=timeout_seconds,
                utf8_input=utf8_input,
                no_bayes=no_bayes,
                adjust_odds=adjust_odds,
                ambiguous_uninomials=ambiguous_uninomials,
                all_matches=all_matches,
                unique_names=unique_names,
                sources=sources,
                words_around=words_around,
            )
        except subprocess.TimeoutExpired:
            logger.error(
                "GNFinder process timed out after %s seconds", timeout_seconds,
            )
            timeout(
                "GNFinder process timed out",
                timeout_seconds=timeout_seconds,
                binary=binary,
            )
        matches = 0
        taxons: list[GNFinderTaxon] = []
        names = result.get("names", [])
        if not isinstance(names, list):
            bad_gateway(
                "GNFinder result has invalid names field",
                field_type=type(names).__name__,
            )
        for name in names:
            if not isinstance(name, dict):
                continue
            matches += 1
            taxons.append(_name_to_taxon(name, verify=verify))
        logger.info(
            "GNFinder extracted %d taxon annotations out of %d names (verify=%s)",
            matches, len(names), verify,
        )
        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count(
            "gnfinder_taxon_matches", matches, lang=lang, verify=str(verify).lower()
        )
        await telemetry.timing("gnfinder_processing_ms", elapsed_ms)
        metadata = result.get("metadata", {})
        await telemetry.info(
            "GNFinder processing completed",
            matches=matches,
            elapsed_ms=elapsed_ms,
            verify=verify,
        )
        logger.info(
            "GNFinder processing completed: matches=%d elapsed_ms=%d",
            matches, elapsed_ms,
        )
        yield DuuiResult.model_construct(
            annotations=taxons,
            feature_structures=[],
            meta=None,
            modification_meta=None,
            errors=[],
            sofa=None,
        )


app = create_app(GNFinderAnnotator, request_adapter=AsyncChunkedRequestAdapter())
