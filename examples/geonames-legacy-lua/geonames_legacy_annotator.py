from __future__ import annotations

from time import time
from urllib.error import URLError
from urllib.request import Request, urlopen

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.lua_custom import LuaCustomCodec
from duui_py.errors import bad_gateway, unavailable, unprocessable
from duui_py.logging import get_event_logger_or_none
from duui_py.metrics import metrics
from duui_py.models import AnnotatorConfig, AnnotatorDescriptor, AnnotatorMeta, Domain, DomainSpec, IODescriptor


class GeoNamesRequest(BaseModel):
    text: str
    max_len: int | None = None
    result_selection: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


def _backend_url(doc: GeoNamesRequest) -> str | None:
    value = doc.parameters.get("backend_url") or os.environ.get("GEONAMES_FST_URL") or os.environ.get("GAZETTEER_RS_URL")
    if value is None:
        return None
    text = str(value).strip()
    return text.rstrip("/") if text else None


def _query_backend(backend_url: str, payload: dict[str, object], timeout_seconds: float) -> object:
    request = Request(
        backend_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


class GeoNamesLegacyAnnotator(DuuiAnnotator[GeoNamesRequest, list[dict[str, object]]]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/gazetteer-rs/variants/geonames legacy Lua migration"}),
        descriptor=AnnotatorDescriptor(
            name="geonames-legacy-lua",
            version="1.5.4",
            input=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json", languages=["x-unspecified"]))),
            output=IODescriptor(
                types={"GeoNamesEntity": ["org.texttechnologylab.annotation.GeoNamesEntity"]},
                text=DomainSpec(default=Domain(mimeType="application/json", languages=["x-unspecified"])),
            ),
        ),
        typesystem_xml_path="TypeSystemGeoNamesLegacy.xml",
        parameters_schema={
            "backend_url": {"type": "string"},
            "timeout": {"type": "number", "default": 120},
            "mode": {"type": "string", "default": "levenshtein"},
            "max_dist": {"type": "integer", "default": 2},
            "min_length": {"type": "integer", "default": 5},
            "result_selection": {"type": "string", "default": "first"},
        },
    )

    def codec(self):
        return LuaCustomCodec(
            (Path(__file__).resolve().parent / "communication.lua").read_text(encoding="utf-8"),
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=lambda body: GeoNamesRequest.model_validate_json(body),
            encode_response=lambda result: json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            name="geonames-legacy-lua",
        )

    async def process(self, doc: GeoNamesRequest) -> list[dict[str, object]]:
        started = time()
        backend_url = _backend_url(doc)
        if backend_url is None:
            unprocessable("GeoNames backend URL is required via parameter 'backend_url', GEONAMES_FST_URL, or GAZETTEER_RS_URL.")
        timeout_seconds = float(doc.parameters.get("timeout") or doc.parameters.get("timeout_seconds") or 120)
        payload: dict[str, object] = {"text": doc.text}
        for key in ("mode", "max_dist", "min_length", "max_len", "state_limit", "result_selection", "filter"):
            if key in doc.parameters:
                payload[key] = doc.parameters[key]
        if doc.max_len is not None:
            payload["max_len"] = doc.max_len
        if doc.result_selection is not None:
            payload["result_selection"] = doc.result_selection

        logger = get_event_logger_or_none()
        if logger is not None:
            await logger.info("GeoNames legacy processing started", extra={"backend_url": backend_url, "text_length": len(doc.text)})
        try:
            response = _query_backend(backend_url, payload, timeout_seconds)
        except (OSError, URLError, TimeoutError) as exc:
            unavailable(f"GeoNames backend request failed: {exc}", backend_url=backend_url)
        except json.JSONDecodeError as exc:
            bad_gateway(f"GeoNames backend returned invalid JSON: {exc}", backend_url=backend_url)
        if not isinstance(response, list):
            bad_gateway("GeoNames backend returned an unexpected JSON root.", json_type=type(response).__name__)

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("geonames_legacy_matches", len(response))
        await metrics.timing("geonames_legacy_processing_ms", elapsed_ms)
        if logger is not None:
            await logger.info("GeoNames legacy processing completed", extra={"matches": len(response), "elapsed_ms": elapsed_ms})
        return [item for item in response if isinstance(item, dict)]


app = create_app(GeoNamesLegacyAnnotator)
