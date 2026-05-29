from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from time import time

from pydantic import BaseModel

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.lua_custom import LuaCustomCodec
from duui_py.errors import bad_gateway, timeout, unavailable
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    Domain,
    DomainSpec,
    IODescriptor,
)
from duui_py.telemetry import telemetry

logger = logging.getLogger(__name__)

DEFAULT_GNFINDER_BINARY = "gnfinder"


class GNFinderLegacyRequest(BaseModel):
    text: str


def _resolve_binary() -> str | None:
    return _resolve_binary_cached()


@lru_cache(maxsize=8)
def _resolve_binary_cached() -> str | None:
    candidates = [
        shutil.which("gnfinder"),
        DEFAULT_GNFINDER_BINARY,
        "/home/stud_homes/s0424382/projects/ttlab/duui/TTLab-UIMA/GNFinder/gnfinder",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _run_gnfinder(binary: str, text: str, timeout_seconds: float) -> dict[str, object]:
    logger.debug("Running gnfinder CLI: binary=%s text_length=%d timeout=%s", binary, len(text), timeout_seconds)
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
        logger.debug("gnfinder CLI completed: returncode=%d", completed.returncode)
    except subprocess.TimeoutExpired as exc:
        logger.error("gnfinder CLI timed out after %s seconds", timeout_seconds)
        timeout(
            "GNFinder process timed out", timeout_seconds=timeout_seconds, binary=binary
        )
        raise exc
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
        logger.error("gnfinder CLI returned unexpected root type: %s", type(parsed).__name__)
        bad_gateway(
            "GNFinder returned an unexpected JSON root", json_type=type(parsed).__name__
        )
    return parsed


def _best_result(name: dict[str, object]) -> dict[str, object] | None:
    verification = name.get("verification")
    if isinstance(verification, dict) and isinstance(
        verification.get("bestResult"), dict
    ):
        return verification["bestResult"]
    return None


class GNFinderLegacyAnnotator(DuuiAnnotator[GNFinderLegacyRequest, dict[str, object]]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(
            meta={"source": "TTLab-UIMA/GNFinder legacy XMI Lua migration"}
        ),
        descriptor=AnnotatorDescriptor(
            name="gnfinder-legacy-lua",
            version="latest",
            input=IODescriptor(
                bytes=DomainSpec(
                    default=Domain(mimeType="application/vnd.apache.uima.xmi+xml")
                )
            ),
            output=IODescriptor(
                types={
                    "Taxon": ["org.texttechnologylab.annotation.type.Taxon"],
                },
                bytes=DomainSpec(
                    default=Domain(mimeType="application/vnd.apache.uima.xmi+xml")
                ),
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
            (Path(__file__).resolve().parent / "communication.lua").read_text(
                encoding="utf-8"
            ),
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=lambda body: GNFinderLegacyRequest.model_validate_json(body),
            encode_response=lambda result: json.dumps(
                result, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8"),
            name="gnfinder-legacy-lua",
        )

    async def process(self, doc: GNFinderLegacyRequest) -> dict[str, object]:
        started = time()
        text = doc.text or ""
        logger.info(
            "GNFinder legacy processing started: text_length=%d",
            len(text),
        )
        binary = _resolve_binary()
        if binary is None:
            logger.error("GNFinder binary not found")
            unavailable(
                "GNFinder binary was not found.",
                binary=DEFAULT_GNFINDER_BINARY,
            )
        logger.debug("GNFinder legacy resolved binary: %s", binary)
        await telemetry.info(
            "GNFinder legacy processing started", binary=binary, text_length=len(text)
        )
        result = _run_gnfinder(binary, text, 120.0)
        names = result.get("names")
        if not isinstance(names, list):
            logger.warning(
                "GNFinder result names field is not a list: type=%s",
                type(names).__name__,
            )
            names = []
        logger.debug("GNFinder returned %d name entries", len(names))
        taxons: list[dict[str, object]] = []
        for item in names:
            if not isinstance(item, dict):
                continue
            begin = item.get("start")
            end = item.get("end")
            if not isinstance(begin, int) or not isinstance(end, int):
                continue
            best = _best_result(item)
            taxon: dict[str, object] = {
                "begin": begin,
                "end": end,
            }
            if best and best.get("currentName") is not None:
                taxon["value"] = str(best["currentName"])
            if best and best.get("outlink") is not None:
                taxon["identifier"] = str(best["outlink"])
            taxons.append(taxon)
        logger.info(
            "GNFinder legacy extracted %d taxon annotations out of %d names",
            len(taxons),
            len(names),
        )
        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count("gnfinder_legacy_taxons", len(taxons))
        await telemetry.timing("gnfinder_legacy_processing_ms", elapsed_ms)
        await telemetry.info(
            "GNFinder legacy processing completed",
            taxons=len(taxons),
            elapsed_ms=elapsed_ms,
        )
        logger.info(
            "GNFinder legacy processing completed: taxons=%d elapsed_ms=%d",
            len(taxons),
            elapsed_ms,
        )
        name = "gnfinder-legacy-lua"
        version = "latest"
        return {
            "taxons": taxons,
            "meta": {
                "name": name,
                "version": version,
                "modelName": "gnfinder",
                "modelVersion": "legacy",
            },
            "modification_meta": {
                "user": name,
                "timestamp": int(time()),
                "comment": f"{name} ({version}), gnfinder ({binary})",
            },
        }


app = create_app(GNFinderLegacyAnnotator)
