from __future__ import annotations
from collections.abc import AsyncIterator
from pathlib import Path
from time import sleep, time
from urllib.error import URLError
from urllib.parse import urlsplit
import asyncio
import atexit
import http.client
import json
import os
import shutil
import subprocess
import threading
from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import bad_gateway, unavailable
from duui_py.logging.core import get_configured_event_logger
from duui_py.telemetry import telemetry
from duui_py.models import (
    AnnotatorConfig, AnnotatorDescriptor, AnnotatorMeta,
    Domain, DomainSpec, DuuiResult, IODescriptor, V1RequestEnvelope,
)
from duui_py.models.uima import sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import Taxon

TAXON_TYPE = Taxon.model_fields["type"].default

DEFAULT_GAZETTEER_RS_PORT = 18001
_BACKEND_LOCK = threading.Lock()
_BACKEND_PROCESS: subprocess.Popen[bytes] | None = None
_BACKEND_URL_CACHE: str | None = None
_HTTP_LOCAL = threading.local()


# ---------------------------------------------------------------------------
# Backend lifecycle
# ---------------------------------------------------------------------------
def _normalize_backend_url(value: str) -> str:
    url = value.rstrip("/")
    return url if url.endswith("/v1/process") else f"{url}/v1/process"


def _gazetteer_binary(required: bool = True) -> str:
    local = Path(__file__).resolve().parent / "backend" / "gazetteer"
    for candidate in (str(local), "/app/gazetteer", shutil.which("gazetteer")):
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    if required:
        unavailable("No bundled gazetteer-rs binary found.")
    return ""


def _gazetteer_config(required: bool = True) -> Path:
    local = Path(__file__).resolve().parent / "backend" / "config.toml"
    for candidate in (str(local), "/app/config.toml", "config.toml"):
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    if required:
        unavailable("No bundled gazetteer-rs config found.")
    return Path("/app/config.toml")


def _stop_local_backend() -> None:
    if _BACKEND_PROCESS is not None and _BACKEND_PROCESS.poll() is None:
        _BACKEND_PROCESS.terminate()


def _ensure_local_backend() -> str:
    global _BACKEND_PROCESS, _BACKEND_URL_CACHE
    port = DEFAULT_GAZETTEER_RS_PORT
    base_url = f"http://127.0.0.1:{port}"
    url = _normalize_backend_url(base_url)
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
                [binary, "--config", str(config), "--address", "127.0.0.1",
                 "--port", str(port), "--workers", "1", "--limit", "536870912"],
                cwd=str(config.parent),
            )
            atexit.register(_stop_local_backend)
        deadline = time() + 120.0
        while time() < deadline:
            if _backend_ready(url):
                _BACKEND_URL_CACHE = url
                return url
            sleep(0.25)
    unavailable("Bundled gazetteer-rs backend did not become ready.", backend_url=url)


# ---------------------------------------------------------------------------
# HTTP query helpers
# ---------------------------------------------------------------------------
def _backend_ready(url: str) -> bool:
    try:
        _query_backend(url, {"text": ""}, 1)
        return True
    except Exception:
        return False


def _http_connection(key: tuple[str, str, int], timeout_seconds: float) -> http.client.HTTPConnection:
    pool = getattr(_HTTP_LOCAL, "pool", None)
    if pool is None:
        pool = {}
        _HTTP_LOCAL.pool = pool
    conn = pool.get(key)
    if conn is not None:
        return conn
    scheme, host, port = key
    conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(host, port, timeout=timeout_seconds)
    pool[key] = conn
    return conn


def _drop_http_connection(key: tuple[str, str, int]) -> None:
    pool = getattr(_HTTP_LOCAL, "pool", None)
    if not isinstance(pool, dict):
        return
    conn = pool.pop(key, None)
    if conn is not None:
        conn.close()


def _query_backend(backend_url: str, payload: dict[str, object], timeout_seconds: float) -> object:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    parsed = urlsplit(backend_url)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    key = (parsed.scheme or "http", parsed.hostname or "127.0.0.1", port)
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Content-Length": str(len(body))}
    for attempt in range(2):
        conn = _http_connection(key, timeout_seconds)
        try:
            conn.request("POST", path, body=body, headers=headers)
            response = conn.getresponse()
            data = response.read()
            if response.status >= 400:
                raise OSError(f"HTTP {response.status} {response.reason}: {data[:256].decode('utf-8', errors='replace')}")
            return json.loads(data.decode("utf-8"))
        except (OSError, http.client.HTTPException):
            _drop_http_connection(key)
            if attempt == 0:
                continue
            raise
    raise OSError("Gazetteer backend request failed after reconnect")


# ===================================================================
# GazetteerAnnotator
# ===================================================================
class GazetteerAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/gazetteer-rs/variants/biofid migration"}),
        descriptor=AnnotatorDescriptor(
            name="gazetteer-msgpack-lua",
            version="1.0.0",
            input=IODescriptor(
                text=DomainSpec(default=Domain(mimeType="text/plain; charset=utf-8", languages=["x-unspecified"])),
            ),
            output=IODescriptor(
                types={"Taxon": [TAXON_TYPE]},
                text=DomainSpec(default=Domain(mimeType="text/plain; charset=utf-8", languages=["x-unspecified"])),
            ),
        ),
        typesystem_xml_path="TypeSystemGazetteer.xml",
        parameters_schema={
            "backend_url": {
                "type": "string",
                "description": "Optional gazetteer-rs backend URL. If omitted, bundled backend is started.",
            },
            "timeout": {"type": "number", "default": 120},
            "max_len": {"type": "integer"},
            "result_selection": {"type": "string"},
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @telemetry.timed("gazetteer_processing_ms", annotator="gazetteer")
    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        logger = get_configured_event_logger()
        started = time()
        if logger is not None:
            await logger.trace("gazetteer process() entry")
            await logger.info("gazetteer process() start")

        text = sofa_text_value(doc.sofa) or ""
        timeout_seconds = float(doc.parameters.get("timeout") or doc.parameters.get("timeout_seconds") or 120)

        if logger is not None:
            await logger.info(f"gazetteer process: text_length={len(text)} timeout={timeout_seconds:.1f}s")

        payload: dict[str, object] = {"text": text}
        for key in ("max_len", "result_selection"):
            if key in doc.parameters:
                payload[key] = doc.parameters[key]

        # -- resolve backend URL -------------------------------------------------
        configured = doc.parameters.get("backend_url")
        if configured and str(configured).strip():
            backend_url = _normalize_backend_url(str(configured).strip())
        elif _BACKEND_URL_CACHE is not None:
            backend_url = _BACKEND_URL_CACHE
        else:
            if logger is not None:
                await logger.info("Starting local gazetteer-rs backend")
            backend_url = await asyncio.to_thread(_ensure_local_backend)

        if logger is not None:
            await logger.info(f"gazetteer invoking backend at {backend_url}")

        await telemetry.trace(
            "Gazetteer process request configured",
            backend_url=backend_url, text_length=len(text), timeout_seconds=timeout_seconds,
        )

        try:
            response = await asyncio.to_thread(_query_backend, backend_url, payload, timeout_seconds)
        except (OSError, URLError, TimeoutError) as exc:
            if logger is not None:
                await logger.error(f"Gazetteer backend request failed: url={backend_url} error={exc}")
            await telemetry.error("Gazetteer backend request failed", backend_url=backend_url, exception=type(exc).__name__)
            unavailable(f"Gazetteer backend request failed: {exc}", backend_url=backend_url)
        except json.JSONDecodeError as exc:
            if logger is not None:
                await logger.error(f"Gazetteer backend invalid JSON: url={backend_url} error={exc}")
            await telemetry.error("Gazetteer backend returned invalid JSON", backend_url=backend_url, exception=type(exc).__name__)
            bad_gateway(f"Gazetteer backend returned invalid JSON: {exc}", backend_url=backend_url)

        if not isinstance(response, list):
            if logger is not None:
                await logger.error(f"Gazetteer backend unexpected root type: {type(response).__name__}")
            await telemetry.error("Gazetteer backend unexpected JSON root", json_type=type(response).__name__, backend_url=backend_url)
            bad_gateway("Gazetteer backend returned unexpected JSON root.", json_type=type(response).__name__)

        # -- parse results -------------------------------------------------------
        taxons: list[Taxon] = []
        skipped = 0
        for item in response:
            if not isinstance(item, dict):
                skipped += 1
                continue
            try:
                begin = int(item["begin"])
                end = int(item["end"])
            except (KeyError, TypeError, ValueError):
                skipped += 1
                continue
            taxons.append(Taxon(
                begin=begin, end=end,
                value=str(item.get("match_strings")) if item.get("match_strings") is not None else None,
                identifier=str(item.get("match_labels")) if item.get("match_labels") is not None else None,
            ))

        if skipped and logger is not None:
            await logger.warning(f"Gazetteer skipped {skipped} malformed results out of {len(response)}")

        elapsed_ms = int((time() - started) * 1000)
        if logger is not None:
            await logger.info(f"gazetteer process() completed: matches={len(taxons)} skipped={skipped} elapsed_ms={elapsed_ms}")

        await telemetry.count("gazetteer_matches", len(taxons))
        await telemetry.debug("Gazetteer processing completed", matches=len(taxons), elapsed_ms=elapsed_ms)

        yield DuuiResult.model_construct(
            annotations=taxons, feature_structures=[], meta=None,
            modification_meta=None, errors=[], sofa=None,
        )


app = create_app(GazetteerAnnotator, request_adapter=AsyncChunkedRequestAdapter())
