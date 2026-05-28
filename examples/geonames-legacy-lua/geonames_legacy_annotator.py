from __future__ import annotations
from time import sleep, time
from urllib.error import URLError
from urllib.request import Request, urlopen
import atexit
import json
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.lua_custom import LuaCustomCodec
from duui_py.errors import bad_gateway, unavailable
from duui_py.telemetry import telemetry
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    Domain,
    DomainSpec,
    IODescriptor,
)


class GeoNamesRequest(BaseModel):
    text: str
    max_len: int | None = None
    result_selection: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


DEFAULT_GEONAMES_FST_PORT = 18001
_BACKEND_LOCK = threading.Lock()
_BACKEND_PROCESS: subprocess.Popen[bytes] | None = None
_BACKEND_URL_CACHE: str | None = None


def _backend_url(doc: GeoNamesRequest) -> str:
    value = doc.parameters.get("backend_url")
    if value is None or not str(value).strip():
        return _ensure_local_backend()
    return _normalize_backend_url(str(value).strip())


def _normalize_backend_url(value: str) -> str:
    url = value.rstrip("/")
    if url.endswith("/v1/process"):
        return url
    return f"{url}/v1/process"


def _ensure_local_backend() -> str:
    global _BACKEND_PROCESS, _BACKEND_URL_CACHE
    port = DEFAULT_GEONAMES_FST_PORT
    url = _normalize_backend_url(f"http://127.0.0.1:{port}")
    if _BACKEND_URL_CACHE is not None:
        return _BACKEND_URL_CACHE
    if _backend_ready(url):
        _BACKEND_URL_CACHE = url
        return url
    with _BACKEND_LOCK:
        if _BACKEND_URL_CACHE is not None:
            return _BACKEND_URL_CACHE
        if _backend_ready(url):
            _BACKEND_URL_CACHE = url
            return url
        if _BACKEND_PROCESS is None or _BACKEND_PROCESS.poll() is not None:
            binary = _gazetteer_binary()
            config = _gazetteer_config()
            _BACKEND_PROCESS = subprocess.Popen(
                [
                    binary,
                    "--config",
                    str(config),
                    "--address",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--workers",
                    "1",
                    "--limit",
                    "536870912",
                ],
                cwd=str(config.parent),
            )
            atexit.register(_stop_local_backend)
        deadline = time() + 20
        while time() < deadline:
            if _backend_ready(url):
                _BACKEND_URL_CACHE = url
                return url
            sleep(0.25)
    unavailable(
        "Bundled GeoNames/gazetteer-rs backend did not become ready.", backend_url=url
    )


def _stop_local_backend() -> None:
    if _BACKEND_PROCESS is not None and _BACKEND_PROCESS.poll() is None:
        _BACKEND_PROCESS.terminate()


def _gazetteer_binary() -> str:
    local = Path(__file__).resolve().parent / "backend" / "gazetteer"
    candidates = [
        str(local),
        "/app/gazetteer",
        shutil.which("gazetteer"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    unavailable(
        "No bundled gazetteer-rs binary found.", candidates=[c for c in candidates if c]
    )


def _gazetteer_config() -> Path:
    local = Path(__file__).resolve().parent / "backend" / "config.toml"
    candidates = [
        str(local),
        "/app/config.toml",
        "config.toml",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    unavailable(
        "No bundled gazetteer-rs config found.", candidates=[c for c in candidates if c]
    )


def _backend_ready(url: str) -> bool:
    try:
        _query_backend(url, {"text": ""}, 1)
        return True
    except Exception:
        return False


def _query_backend(
    backend_url: str, payload: dict[str, object], timeout_seconds: float
) -> object:
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
        meta=AnnotatorMeta(
            meta={
                "source": "TTLab-UIMA/gazetteer-rs/variants/geonames legacy Lua migration"
            }
        ),
        descriptor=AnnotatorDescriptor(
            name="geonames-legacy-lua",
            version="1.5.4",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="application/json", languages=["x-unspecified"]
                    )
                )
            ),
            output=IODescriptor(
                types={
                    "GeoNamesEntity": [
                        "org.texttechnologylab.annotation.GeoNamesEntity"
                    ]
                },
                text=DomainSpec(
                    default=Domain(
                        mimeType="application/json", languages=["x-unspecified"]
                    )
                ),
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
            (Path(__file__).resolve().parent / "communication.lua").read_text(
                encoding="utf-8"
            ),
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=lambda body: GeoNamesRequest.model_validate_json(body),
            encode_response=lambda result: json.dumps(
                result, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8"),
            name="geonames-legacy-lua",
        )

    async def process(self, doc: GeoNamesRequest) -> list[dict[str, object]]:
        started = time()
        backend_url = _backend_url(doc)
        timeout_seconds = float(
            doc.parameters.get("timeout")
            or doc.parameters.get("timeout_seconds")
            or 120
        )
        payload: dict[str, object] = {
            "text": doc.text,
            "mode": "levenshtein",
            "max_dist": 2,
            "min_length": 5,
        }
        for key in (
            "mode",
            "max_dist",
            "min_length",
            "max_len",
            "state_limit",
            "result_selection",
            "filter",
        ):
            if key in doc.parameters:
                payload[key] = doc.parameters[key]
        if doc.max_len is not None:
            payload["max_len"] = doc.max_len
        if doc.result_selection is not None:
            payload["result_selection"] = doc.result_selection
        await telemetry.info(
            "GeoNames legacy processing started",
            backend_url=backend_url,
            text_length=len(doc.text),
        )
        try:
            response = _query_backend(backend_url, payload, timeout_seconds)
        except (OSError, URLError, TimeoutError) as exc:
            unavailable(
                f"GeoNames backend request failed: {exc}", backend_url=backend_url
            )
        except json.JSONDecodeError as exc:
            bad_gateway(
                f"GeoNames backend returned invalid JSON: {exc}",
                backend_url=backend_url,
            )
        if not isinstance(response, list):
            bad_gateway(
                "GeoNames backend returned an unexpected JSON root.",
                json_type=type(response).__name__,
            )
        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count("geonames_legacy_matches", len(response))
        await telemetry.timing("geonames_legacy_processing_ms", elapsed_ms)
        await telemetry.info(
            "GeoNames legacy processing completed",
            matches=len(response),
            elapsed_ms=elapsed_ms,
        )
        return [item for item in response if isinstance(item, dict)]


app = create_app(GeoNamesLegacyAnnotator)
