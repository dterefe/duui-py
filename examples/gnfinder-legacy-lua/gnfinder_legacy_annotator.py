from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.lua_custom import LuaCustomCodec
from duui_py.errors import bad_gateway, timeout, unavailable
from duui_py.logging import get_event_logger_or_none
from duui_py.metrics import metrics
from duui_py.models import AnnotatorConfig, AnnotatorDescriptor, AnnotatorMeta, Domain, DomainSpec, IODescriptor


DEFAULT_GNFINDER_BINARY = "gnfinder"


def _resolve_binary() -> str | None:
    candidates = [
        os.getenv("GNFINDER_BINARY"),
        shutil.which("gnfinder"),
        DEFAULT_GNFINDER_BINARY,
        "/home/stud_homes/s0424382/projects/ttlab/duui/TTLab-UIMA/GNFinder/gnfinder",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _run_gnfinder(binary: str, text: str, timeout_seconds: float) -> dict[str, object]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(text)
        input_path = handle.name
    try:
        completed = subprocess.run(
            [binary, input_path, "-v", "-f", "compact"],
            capture_output=True,
            check=False,
            encoding="utf-8",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        timeout("GNFinder process timed out", timeout_seconds=timeout_seconds, binary=binary)
        raise exc
    finally:
        Path(input_path).unlink(missing_ok=True)

    if completed.returncode != 0:
        bad_gateway("GNFinder process failed", returncode=completed.returncode, stderr=completed.stderr.strip())
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        bad_gateway("GNFinder returned invalid JSON", error=str(exc))
    if not isinstance(parsed, dict):
        bad_gateway("GNFinder returned an unexpected JSON root", json_type=type(parsed).__name__)
    return parsed


def _load_cassis():
    try:
        from cassis import load_cas_from_xmi, load_typesystem
    except Exception as exc:  # noqa: BLE001
        unavailable("dkpro-cassis is required for the legacy GNFinder XMI transport.", exception=type(exc).__name__)
    return load_cas_from_xmi, load_typesystem


def _text_from_cas(cas: object) -> str:
    value = getattr(cas, "sofa_string", None)
    if value is not None:
        return str(value)
    sofa = getattr(cas, "sofa", None)
    sofa_string = getattr(sofa, "sofaString", None)
    return str(sofa_string or "")


def _best_result(name: dict[str, object]) -> dict[str, object] | None:
    verification = name.get("verification")
    if isinstance(verification, dict) and isinstance(verification.get("bestResult"), dict):
        return verification["bestResult"]
    return None


class GNFinderLegacyAnnotator(DuuiAnnotator[bytes, bytes]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/GNFinder legacy XMI Lua migration"}),
        descriptor=AnnotatorDescriptor(
            name="gnfinder-legacy-lua",
            version="latest",
            input=IODescriptor(bytes=DomainSpec(default=Domain(mimeType="application/vnd.apache.uima.xmi+xml"))),
            output=IODescriptor(
                types={
                    "Taxon": ["org.texttechnologylab.annotation.type.Taxon"],
                    "AnnotationComment": ["org.texttechnologylab.annotation.AnnotationComment"],
                },
                bytes=DomainSpec(default=Domain(mimeType="application/vnd.apache.uima.xmi+xml")),
            ),
        ),
        typesystem_xml_path="TypeSystemGNFinderLegacy.xml",
        parameters_schema={
            "timeout": {"type": "number", "default": 120},
            "gnfinder_binary": {"type": "string"},
        },
    )

    def codec(self):
        return LuaCustomCodec(
            (Path(__file__).resolve().parent / "communication.lua").read_text(encoding="utf-8"),
            request_media_type="application/vnd.apache.uima.xmi+xml",
            response_media_type="application/vnd.apache.uima.xmi+xml",
            decode_request=lambda body: body,
            encode_response=lambda body: body,
            name="gnfinder-legacy-lua",
        )

    async def process(self, doc: bytes) -> bytes:
        started = time()
        load_cas_from_xmi, load_typesystem = _load_cassis()
        with open(Path(__file__).resolve().parent / "TypeSystemGNFinderLegacy.xml", "rb") as handle:
            typesystem = load_typesystem(handle)
        try:
            cas = load_cas_from_xmi(BytesIO(doc), typesystem=typesystem, lenient=True)
        except Exception as exc:  # noqa: BLE001
            bad_gateway("Legacy GNFinder request XMI could not be decoded.", exception=type(exc).__name__, detail=str(exc))

        text = _text_from_cas(cas)
        binary = _resolve_binary()
        if binary is None:
            unavailable("GNFinder binary was not found.", binary=os.getenv("GNFINDER_BINARY") or DEFAULT_GNFINDER_BINARY)

        logger = get_event_logger_or_none()
        if logger is not None:
            await logger.info("GNFinder legacy processing started", extra={"binary": binary, "text_length": len(text)})

        result = _run_gnfinder(binary, text, float(os.getenv("GNFINDER_TIMEOUT_SECONDS", "120")))
        names = result.get("names")
        if not isinstance(names, list):
            names = []

        taxon_type = typesystem.get_type("org.texttechnologylab.annotation.type.Taxon")
        comment_type = typesystem.get_type("org.texttechnologylab.annotation.AnnotationComment")
        added = 0
        for item in names:
            if not isinstance(item, dict):
                continue
            begin = item.get("start")
            end = item.get("end")
            if not isinstance(begin, int) or not isinstance(end, int):
                continue
            best = _best_result(item)
            taxon = taxon_type(
                begin=begin,
                end=end,
                value=str(best.get("currentName")) if best and best.get("currentName") is not None else None,
                identifier=str(best.get("outlink")) if best and best.get("outlink") is not None else None,
            )
            cas.add_annotation(taxon)
            verification = item.get("verification")
            comment_value = json.dumps(best if best is not None else verification, ensure_ascii=False)
            cas.add_annotation(comment_type(reference=taxon, key="gnfinder_verification", value=comment_value))
            added += 1

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("gnfinder_legacy_taxons", added)
        await metrics.timing("gnfinder_legacy_processing_ms", elapsed_ms)
        if logger is not None:
            await logger.info("GNFinder legacy processing completed", extra={"taxons": added, "elapsed_ms": elapsed_ms})
        return cas.to_xmi().encode("utf-8")


app = create_app(GNFinderLegacyAnnotator)
