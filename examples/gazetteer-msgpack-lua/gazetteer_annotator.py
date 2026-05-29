from __future__ import annotations
from collections.abc import AsyncIterator
from pathlib import Path
from time import sleep, time
from urllib.error import URLError
from urllib.parse import urlsplit
import atexit
import asyncio
import http.client
import json
import logging
import os
import shutil
import subprocess
import threading
from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import bad_gateway, unavailable
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
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import Taxon

TAXON_TYPE = Taxon.model_fields["type"].default

logger = logging.getLogger(__name__)

DEFAULT_GAZETTEER_RS_PORT = 18001
_BACKEND_LOCK = threading.Lock()
_BACKEND_PROCESS: subprocess.Popen[bytes] | None = None
_BACKEND_URL_CACHE: str | None = None
_HTTP_LOCAL = threading.local()


def _configured_backend_url(parameters: dict[str, object]) -> str | None:
    value = parameters.get("backend_url")
    if value is None or not str(value).strip():
        logger.debug("No backend_url parameter configured, will use local backend")
        return None
    url = _normalize_backend_url(str(value).strip())
    logger.info("Using configured backend_url: %s", url)
    return url


async def _resolve_backend_url(parameters: dict[str, object]) -> str:
    logger.debug("Resolving gazetteer-rs backend URL")
    configured = _configured_backend_url(parameters)
    if configured is not None:
        logger.debug("Resolved backend via configured URL: %s", configured)
        return configured
    if _BACKEND_URL_CACHE is not None:
        logger.debug("Resolved backend from cache: %s", _BACKEND_URL_CACHE)
        return _BACKEND_URL_CACHE
    logger.info("No configured or cached backend, starting local gazetteer-rs")
    return await asyncio.to_thread(_ensure_local_backend)


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
            cwd = str(config.parent)
            command = [
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
            ]
            logger.info(
                "Starting local gazetteer-rs backend: binary=%s config=%s port=%d",
                binary, str(config), port,
            )
            _BACKEND_PROCESS = subprocess.Popen(command, cwd=cwd)
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
    unavailable(
        "Bundled gazetteer-rs backend did not become ready.",
        backend_url=url,
        binary=_gazetteer_binary(required=False),
        config=str(_gazetteer_config(required=False)),
    )


def _stop_local_backend() -> None:
    if _BACKEND_PROCESS is not None and _BACKEND_PROCESS.poll() is None:
        logger.info("Stopping local gazetteer-rs backend (pid=%d)", _BACKEND_PROCESS.pid)
        _BACKEND_PROCESS.terminate()


def _gazetteer_binary(required: bool = True) -> str:
    local = Path(__file__).resolve().parent / "backend" / "gazetteer"
    candidates = [str(local), "/app/gazetteer", shutil.which("gazetteer")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    if required:
        unavailable(
            "No bundled gazetteer-rs binary found.",
            candidates=[candidate for candidate in candidates if candidate],
        )
    return ""


def _gazetteer_config(required: bool = True) -> Path:
    local = Path(__file__).resolve().parent / "backend" / "config.toml"
    candidates = [str(local), "/app/config.toml", "config.toml"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    if required:
        unavailable(
            "No bundled gazetteer-rs config found.",
            candidates=[candidate for candidate in candidates if candidate],
        )
    return Path("/app/config.toml")


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
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    parsed = urlsplit(backend_url)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    key = (parsed.scheme or "http", parsed.hostname or "127.0.0.1", port)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Length": str(len(body)),
    }
    for attempt in range(2):
        conn = _http_connection(key, timeout_seconds)
        try:
            conn.request("POST", path, body=body, headers=headers)
            response = conn.getresponse()
            data = response.read()
            if response.status >= 400:
                logger.error(
                    "Gazetteer-rs backend HTTP error: status=%d reason=%s",
                    response.status, response.reason,
                )
                raise OSError(
                    f"HTTP {response.status} {response.reason}: "
                    f"{data[:256].decode('utf-8', errors='replace')}"
                )
            result = json.loads(data.decode("utf-8"))
            logger.debug(
                "Gazetteer-rs backend returned %d results",
                len(result) if isinstance(result, list) else -1,
            )
            return result
        except (OSError, http.client.HTTPException) as exc:
            logger.warning(
                "Gazetteer-rs backend request attempt %d failed: %s",
                attempt + 1, exc,
            )
            _drop_http_connection(key)
            if attempt == 0:
                continue
            raise
    raise OSError("Gazetteer backend request failed after reconnect")


def _http_connection(
    key: tuple[str, str, int], timeout_seconds: float
) -> http.client.HTTPConnection:
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


class GazetteerAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(
            meta={"source": "TTLab-UIMA/gazetteer-rs/variants/biofid migration"}
        ),
        descriptor=AnnotatorDescriptor(
            name="gazetteer-msgpack-lua",
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
                types={"Taxon": [TAXON_TYPE]},
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemGazetteer.xml",
        parameters_schema={
            "backend_url": {
                "type": "string",
                "description": "Optional override for a gazetteer-rs/biofid-compatible backend URL. If omitted, the bundled backend is started.",
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
        started = time()
        logger.info("gazetteer process() start")
        text = sofa_text_value(doc.sofa) or ""
        timeout_seconds = float(
            doc.parameters.get("timeout")
            or doc.parameters.get("timeout_seconds")
            or 120
        )
        logger.debug(
            "gazetteer process: text_length=%d timeout=%.1fs params=%s",
            len(text), timeout_seconds,
            {k: v for k, v in doc.parameters.items() if k != "text"},
        )
        payload: dict[str, object] = {"text": text}
        for key in ("max_len", "result_selection"):
            if key in doc.parameters:
                payload[key] = doc.parameters[key]
                logger.debug("gazetteer payload param: %s=%s", key, doc.parameters[key])

        backend_url = await _resolve_backend_url(doc.parameters)
        logger.info("gazetteer invoking backend at %s", backend_url)
        await telemetry.trace(
            "Gazetteer process request configured",
            backend_url=backend_url,
            text_length=len(text),
            timeout_seconds=timeout_seconds,
        )

        try:
            response = await asyncio.to_thread(
                _query_backend, backend_url, payload, timeout_seconds
            )
        except (OSError, URLError, TimeoutError) as exc:
            logger.error(
                "Gazetteer backend request failed: url=%s error=%s",
                backend_url, exc,
            )
            await telemetry.error(
                "Gazetteer backend request failed",
                backend_url=backend_url,
                exception=type(exc).__name__,
            )
            unavailable(
                f"Gazetteer backend request failed: {exc}", backend_url=backend_url
            )
        except json.JSONDecodeError as exc:
            logger.error(
                "Gazetteer backend returned invalid JSON: url=%s error=%s",
                backend_url, exc,
            )
            await telemetry.error(
                "Gazetteer backend returned invalid JSON",
                backend_url=backend_url,
                exception=type(exc).__name__,
            )
            bad_gateway(
                f"Gazetteer backend returned invalid JSON: {exc}",
                backend_url=backend_url,
            )
        if not isinstance(response, list):
            logger.error(
                "Gazetteer backend unexpected JSON root type: %s",
                type(response).__name__,
            )
            await telemetry.error(
                "Gazetteer backend returned unexpected JSON root",
                json_type=type(response).__name__,
                backend_url=backend_url,
            )
            bad_gateway(
                "Gazetteer backend returned an unexpected JSON root.",
                json_type=type(response).__name__,
            )

        logger.debug("Parsing %d gazetteer results into Taxon annotations", len(response))
        taxons: list[Taxon] = []
        skipped = 0
        for item in response:
            if not isinstance(item, dict):
                skipped += 1
                logger.debug("Skipping non-dict gazetteer result item: %s", type(item).__name__)
                continue
            try:
                begin = int(item["begin"])
                end = int(item["end"])
            except (KeyError, TypeError, ValueError) as exc:
                skipped += 1
                logger.debug(
                    "Skipping gazetteer result with invalid begin/end: %s", exc,
                )
                continue
            value = item.get("match_strings")
            identifier = item.get("match_labels")
            taxons.append(
                Taxon(
                    begin=begin,
                    end=end,
                    value=str(value) if value is not None else None,
                    identifier=str(identifier) if identifier is not None else None,
                )
            )
        if skipped:
            logger.warning(
                "Gazetteer skipped %d malformed results out of %d",
                skipped, len(response),
            )
            await telemetry.warning(
                "Gazetteer skipped malformed backend matches",
                skipped=skipped,
                returned=len(response),
            )
        elapsed_ms = int((time() - started) * 1000)
        logger.info(
            "gazetteer process() completed: matches=%d skipped=%d elapsed_ms=%d",
            len(taxons), skipped, elapsed_ms,
        )
        await telemetry.count("gazetteer_matches", len(taxons))
        await telemetry.debug(
            "Gazetteer processing completed",
            matches=len(taxons),
            elapsed_ms=elapsed_ms,
        )
        yield DuuiResult.model_construct(
            annotations=taxons,
            feature_structures=[],
            meta=None,
            modification_meta=None,
            errors=[],
            sofa=None,
        )

app = create_app(GazetteerAnnotator, request_adapter=AsyncChunkedRequestAdapter())
