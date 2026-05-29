from __future__ import annotations
from time import sleep, time
from urllib.error import URLError
from urllib.request import Request, urlopen
import atexit
import asyncio
import json
import logging
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


class GazetteerRequest(BaseModel):
    text: str
    max_len: int | None = None
    result_selection: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


logger = logging.getLogger(__name__)

DEFAULT_GAZETTEER_RS_PORT = 18001
_BACKEND_LOCK = threading.Lock()
_BACKEND_PROCESS: subprocess.Popen[bytes] | None = None
_BACKEND_URL_CACHE: str | None = None


def _backend_url(doc: GazetteerRequest) -> str:
    value = doc.parameters.get("backend_url")
    if value is None or not str(value).strip():
        logger.debug("No backend_url configured, using local backend")
        return _ensure_local_backend()
    url = _normalize_backend_url(str(value).strip())
    logger.info("Using configured backend_url: %s", url)
    return url


def _normalize_backend_url(value: str) -> str:
    url = value.rstrip("/")
    if url.endswith("/v1/process"):
        return url
    return f"{url}/v1/process"


def _ensure_local_backend() -> str:
    global _BACKEND_PROCESS, _BACKEND_URL_CACHE
    port = DEFAULT_GAZETTEER_RS_PORT
    base_url = f"http://127.0.0.1:{port}"
    url = _normalize_backend_url(base_url)
    if _BACKEND_URL_CACHE is not None:
        logger.debug("Local backend URL already cached: %s", _BACKEND_URL_CACHE)
        return _BACKEND_URL_CACHE
    if _backend_ready(url):
        logger.info("Local gazetteer-rs backend already running at %s", url)
        _BACKEND_URL_CACHE = url
        return url
    with _BACKEND_LOCK:
        if _BACKEND_URL_CACHE is not None:
            logger.debug("Local backend URL cached under lock: %s", _BACKEND_URL_CACHE)
            return _BACKEND_URL_CACHE
        if _backend_ready(url):
            logger.info("Local gazetteer-rs backend became ready under lock at %s", url)
            _BACKEND_URL_CACHE = url
            return url
        if _BACKEND_PROCESS is None or _BACKEND_PROCESS.poll() is not None:
            binary = _gazetteer_binary()
            config = _gazetteer_config()
            logger.info(
                "Starting local gazetteer-rs backend: binary=%s config=%s port=%d",
                binary, str(config), port,
            )
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
        startup_timeout = 120.0
        deadline = time() + startup_timeout
        logger.debug(
            "Waiting for gazetteer-rs backend to become ready (timeout=%.1fs)",
            startup_timeout,
        )
        while time() < deadline:
            if _backend_ready(url):
                logger.info(
                    "Local gazetteer-rs backend ready after %.1fs",
                    time() - (deadline - startup_timeout),
                )
                _BACKEND_URL_CACHE = url
                return url
            sleep(0.25)
        logger.error(
            "Local gazetteer-rs backend did not become ready within %.1fs",
            startup_timeout,
        )
    unavailable("Bundled gazetteer-rs backend did not become ready.", backend_url=url)


def _stop_local_backend() -> None:
    if _BACKEND_PROCESS is not None and _BACKEND_PROCESS.poll() is None:
        logger.info("Stopping local gazetteer-rs backend (pid=%d)", _BACKEND_PROCESS.pid)
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
    text_len = len(str(payload.get("text", "")))
    logger.debug(
        "Querying gazetteer-rs backend: url=%s text_length=%d timeout=%.1fs",
        backend_url, text_len, timeout_seconds,
    )
    request = Request(
        backend_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        result = json.loads(response.read().decode("utf-8"))
        logger.debug(
            "Gazetteer-rs backend returned %d results",
            len(result) if isinstance(result, list) else -1,
        )
        return result


class GazetteerLegacyAnnotator(
    DuuiAnnotator[GazetteerRequest, list[dict[str, object]]]
):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(
            meta={
                "source": "TTLab-UIMA/gazetteer-rs/variants/biofid legacy Lua migration"
            }
        ),
        descriptor=AnnotatorDescriptor(
            name="gazetteer-legacy-lua",
            version="1.5.4",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="application/json", languages=["x-unspecified"]
                    )
                )
            ),
            output=IODescriptor(
                types={"Taxon": ["org.texttechnologylab.annotation.type.Taxon"]},
                text=DomainSpec(
                    default=Domain(
                        mimeType="application/json", languages=["x-unspecified"]
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemGazetteerLegacy.xml",
        parameters_schema={
            "backend_url": {"type": "string"},
            "timeout": {"type": "number", "default": 120},
            "max_len": {"type": "integer"},
            "result_selection": {"type": "string"},
        },
    )

    def codec(self):
        return LuaCustomCodec(
            (Path(__file__).resolve().parent / "communication.lua").read_text(
                encoding="utf-8"
            ),
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=lambda body: GazetteerRequest.model_validate_json(body),
            encode_response=lambda result: json.dumps(
                result, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8"),
            name="gazetteer-legacy-lua",
        )

    @telemetry.timed("gazetteer_legacy_processing_ms", annotator="gazetteer-legacy")
    async def process(self, doc: GazetteerRequest) -> list[dict[str, object]]:
        started = time()
        logger.info("gazetteer-legacy process() start")
        timeout_seconds = float(
            doc.parameters.get("timeout")
            or doc.parameters.get("timeout_seconds")
            or 120
        )
        logger.debug(
            "gazetteer-legacy process: text_length=%d timeout=%.1fs max_len=%s result_selection=%s",
            len(doc.text), timeout_seconds, doc.max_len, doc.result_selection,
        )
        payload: dict[str, object] = {"text": doc.text}
        if doc.max_len is not None:
            payload["max_len"] = doc.max_len
        if doc.result_selection is not None:
            payload["result_selection"] = doc.result_selection

        @telemetry.timed("gazetteer_legacy_backend_resolve_ms", annotator="gazetteer-legacy")
        async def resolve_backend() -> str:
            return await asyncio.to_thread(_backend_url, doc)

        backend_url = await resolve_backend()
        logger.info("gazetteer-legacy invoking backend at %s", backend_url)
        await telemetry.trace(
            "Gazetteer legacy process request configured",
            backend_url=backend_url,
            text_length=len(doc.text),
            timeout_seconds=timeout_seconds,
        )

        @telemetry.timed("gazetteer_legacy_backend_request_ms", annotator="gazetteer-legacy")
        async def request_backend() -> object:
            return await asyncio.to_thread(_query_backend, backend_url, payload, timeout_seconds)

        try:
            response = await request_backend()
        except (OSError, URLError, TimeoutError) as exc:
            logger.error(
                "Gazetteer legacy backend request failed: url=%s error=%s",
                backend_url, exc,
            )
            await telemetry.error(
                "Gazetteer legacy backend request failed",
                backend_url=backend_url,
                exception=type(exc).__name__,
            )
            unavailable(
                f"Gazetteer backend request failed: {exc}", backend_url=backend_url
            )
        except json.JSONDecodeError as exc:
            logger.error(
                "Gazetteer legacy backend returned invalid JSON: url=%s error=%s",
                backend_url, exc,
            )
            await telemetry.error(
                "Gazetteer legacy backend returned invalid JSON",
                backend_url=backend_url,
                exception=type(exc).__name__,
            )
            bad_gateway(
                f"Gazetteer backend returned invalid JSON: {exc}",
                backend_url=backend_url,
            )
        if not isinstance(response, list):
            logger.error(
                "Gazetteer legacy backend unexpected JSON root type: %s",
                type(response).__name__,
            )
            await telemetry.error(
                "Gazetteer legacy backend returned unexpected JSON root",
                backend_url=backend_url,
                json_type=type(response).__name__,
            )
            bad_gateway(
                "Gazetteer backend returned an unexpected JSON root.",
                json_type=type(response).__name__,
            )

        logger.debug("Filtering %d gazetteer legacy results", len(response))
        filtered = [item for item in response if isinstance(item, dict)]
        skipped = len(response) - len(filtered)
        if skipped:
            logger.warning(
                "Gazetteer legacy skipped %d non-dict results out of %d",
                skipped, len(response),
            )
        elapsed_ms = int((time() - started) * 1000)
        logger.info(
            "gazetteer-legacy process() completed: matches=%d skipped=%d elapsed_ms=%d",
            len(filtered), skipped, elapsed_ms,
        )
        await telemetry.count("gazetteer_legacy_matches", len(filtered))
        await telemetry.debug(
            "Gazetteer legacy processing completed",
            matches=len(filtered),
            elapsed_ms=elapsed_ms,
        )
        return filtered


app = create_app(GazetteerLegacyAnnotator)
