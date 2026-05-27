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


DEFAULT_GAZETTEER_RS_PORT = 18001
_BACKEND_LOCK = threading.Lock()
_BACKEND_PROCESS: subprocess.Popen[bytes] | None = None
_BACKEND_URL_CACHE: str | None = None
_HTTP_LOCAL = threading.local()


def _configured_backend_url(parameters: dict[str, object]) -> str | None:
    value = parameters.get("backend_url") or os.environ.get("GAZETTEER_RS_URL")
    if value is None or not str(value).strip():
        return None
    return _normalize_backend_url(str(value).strip())


async def _resolve_backend_url(parameters: dict[str, object]) -> str:
    configured = _configured_backend_url(parameters)
    if configured is not None:
        return configured
    if _BACKEND_URL_CACHE is not None:
        return _BACKEND_URL_CACHE
    return await asyncio.to_thread(_ensure_local_backend)


def _normalize_backend_url(value: str) -> str:
    url = value.rstrip("/")
    if url.endswith("/v1/process"):
        return url
    return f"{url}/v1/process"


def _ensure_local_backend() -> str:
    global _BACKEND_PROCESS, _BACKEND_URL_CACHE
    port = int(os.environ.get("GAZETTEER_RS_PORT", DEFAULT_GAZETTEER_RS_PORT))
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
                str(os.environ.get("GAZETTEER_RS_WORKERS", "1")),
                "--limit",
                str(os.environ.get("GAZETTEER_RS_LIMIT", "536870912")),
            ]
            _BACKEND_PROCESS = subprocess.Popen(command, cwd=cwd)
            atexit.register(_stop_local_backend)
        startup_timeout = float(os.environ.get("GAZETTEER_RS_STARTUP_TIMEOUT", "120"))
        deadline = time() + startup_timeout
        while time() < deadline:
            if _backend_ready(url):
                _BACKEND_URL_CACHE = url
                return url
            sleep(0.25)
    unavailable(
        "Bundled gazetteer-rs backend did not become ready.",
        backend_url=url,
        binary=_gazetteer_binary(required=False),
        config=str(_gazetteer_config(required=False)),
    )


def _stop_local_backend() -> None:
    if _BACKEND_PROCESS is not None and _BACKEND_PROCESS.poll() is None:
        _BACKEND_PROCESS.terminate()


def _gazetteer_binary(required: bool = True) -> str:
    configured = os.environ.get("GAZETTEER_RS_BINARY")
    local = Path(__file__).resolve().parent / "backend" / "gazetteer"
    candidates = [configured, str(local), "/app/gazetteer", shutil.which("gazetteer")]
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
    configured = os.environ.get("GAZETTEER_RS_CONFIG")
    local = Path(__file__).resolve().parent / "backend" / "config.toml"
    candidates = [configured, str(local), "/app/config.toml", "config.toml"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    if required:
        unavailable(
            "No bundled gazetteer-rs config found.",
            candidates=[candidate for candidate in candidates if candidate],
        )
    return Path(configured or "/app/config.toml")


def _backend_ready(url: str) -> bool:
    try:
        _query_backend(url, {"text": ""}, 1)
        return True
    except Exception:
        return False


def _query_backend(
    backend_url: str, payload: dict[str, object], timeout_seconds: float
) -> object:
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
                raise OSError(
                    f"HTTP {response.status} {response.reason}: "
                    f"{data[:256].decode('utf-8', errors='replace')}"
                )
            return json.loads(data.decode("utf-8"))
        except (OSError, http.client.HTTPException):
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
        text = sofa_text_value(doc.sofa) or ""
        timeout_seconds = float(
            doc.parameters.get("timeout")
            or doc.parameters.get("timeout_seconds")
            or 120
        )
        payload: dict[str, object] = {"text": text}
        for key in ("max_len", "result_selection"):
            if key in doc.parameters:
                payload[key] = doc.parameters[key]

        backend_url = await _resolve_backend_url(doc.parameters)
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
            await telemetry.error(
                "Gazetteer backend request failed",
                backend_url=backend_url,
                exception=type(exc).__name__,
            )
            unavailable(
                f"Gazetteer backend request failed: {exc}", backend_url=backend_url
            )
        except json.JSONDecodeError as exc:
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
            await telemetry.error(
                "Gazetteer backend returned unexpected JSON root",
                json_type=type(response).__name__,
                backend_url=backend_url,
            )
            bad_gateway(
                "Gazetteer backend returned an unexpected JSON root.",
                json_type=type(response).__name__,
            )

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
            await telemetry.warning(
                "Gazetteer skipped malformed backend matches",
                skipped=skipped,
                returned=len(response),
            )
        elapsed_ms = int((time() - started) * 1000)
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
