from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from time import perf_counter, sleep, time
from urllib.error import URLError
from urllib.request import Request, urlopen
import atexit
import http.client
import json
import os
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
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.ner.type.types import (
    Location,
    NamedEntity,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import (
    GeoNamesEntity as LegacyGeoNamesEntity,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.geonames.types import (
    GeoNamesEntity as RichGeoNamesEntity,
)
from urllib.parse import urlsplit

LEGACY_GEONAMES_TYPE = LegacyGeoNamesEntity.model_fields["type"].default
RICH_GEONAMES_TYPE = RichGeoNamesEntity.model_fields["type"].default
LOCATION_TYPE = Location.model_fields["type"].default
NAMED_ENTITY_TYPE = NamedEntity.model_fields["type"].default
DEFAULT_GEONAMES_FST_PORT = 18001
_BACKEND_LOCK = threading.Lock()
_BACKEND_PROCESS: subprocess.Popen[bytes] | None = None
_BACKEND_URL_CACHE: str | None = None
_HTTP_LOCAL = threading.local()


def _configured_backend_url(parameters: dict[str, object]) -> str | None:
    value = (
        parameters.get("backend_url")
        or os.environ.get("GEONAMES_FST_URL")
    )
    if value is None or not str(value).strip():
        return None
    return str(value).strip().rstrip("/")


async def _resolve_backend_url(parameters: dict[str, object]) -> str:
    configured = _configured_backend_url(parameters)
    if configured is not None:
        return configured
    if _BACKEND_URL_CACHE is not None:
        return _BACKEND_URL_CACHE
    return await asyncio.to_thread(_ensure_local_backend)


def _ensure_local_backend() -> str:
    global _BACKEND_PROCESS, _BACKEND_URL_CACHE
    port = int(os.environ.get("GEONAMES_FST_PORT", DEFAULT_GEONAMES_FST_PORT))
    url = f"http://127.0.0.1:{port}"
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
            binary = _geonames_fst_binary()
            data_root = _geonames_data_root()
            command = [
                binary,
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                str(data_root / "geonames"),
                "--alternate",
                str(data_root / "alternateNames"),
                "--timestamp",
                str(data_root / "geonames_timestamp.txt"),
                "--workers",
                str(os.environ.get("GEONAMES_FST_WORKERS", "1")),
            ]
            _BACKEND_PROCESS = subprocess.Popen(command, cwd=str(data_root.parent))
            atexit.register(_stop_local_backend)
        deadline = time() + 20
        while time() < deadline:
            if _backend_ready(url):
                _BACKEND_URL_CACHE = url
                return url
            sleep(0.25)
    unavailable(
        "Bundled GeoNames/gazetteer-rs backend did not become ready.",
        backend_url=url,
        binary=_geonames_fst_binary(required=False),
        data=str(_geonames_data_root(required=False)),
    )


def _stop_local_backend() -> None:
    if _BACKEND_PROCESS is not None and _BACKEND_PROCESS.poll() is None:
        _BACKEND_PROCESS.terminate()


def _geonames_fst_binary(required: bool = True) -> str:
    configured = os.environ.get("GEONAMES_FST_BINARY")
    local = Path(__file__).resolve().parent / "backend" / "geonames-fst"
    candidates = [configured, str(local), "/app/geonames-fst"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    if required:
        unavailable(
            "No bundled geonames-fst binary found.",
            candidates=[candidate for candidate in candidates if candidate],
        )
    return ""


def _geonames_data_root(required: bool = True) -> Path:
    configured = os.environ.get("GEONAMES_FST_DATA")
    local = Path(__file__).resolve().parent / "backend" / "data"
    candidates = [configured, str(local), "/app/data"]
    for candidate in candidates:
        if candidate and (Path(candidate) / "geonames").is_dir():
            return Path(candidate).resolve()
    if required:
        unavailable(
            "No bundled geonames-fst data directory found.",
            candidates=[candidate for candidate in candidates if candidate],
        )
    return Path(configured or "/app/data")


def _backend_ready(url: str) -> bool:
    try:
        _query_backend(
            url,
            {
                "mode": "find",
                "result_selection": "first",
                "queries": [{"reference": "1", "text": "Berlin"}],
            },
            1,
        )
        return True
    except Exception:
        return False


def _query_backend(
    backend_url: str, payload: dict[str, object], timeout_seconds: float
) -> object:
    return _post_json(
        backend_url.rstrip("/") + "/v1/process",
        payload,
        timeout_seconds,
    )


def _post_json(url: str, payload: dict[str, object], timeout_seconds: float) -> object:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    parsed = urlsplit(url)
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
    last_error: Exception | None = None
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
        except (OSError, http.client.HTTPException) as exc:
            _drop_http_connection(key)
            last_error = exc
            if attempt == 0:
                continue
            raise
    assert last_error is not None
    raise last_error


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


def _first_label(value: object) -> tuple[int | None, str | None, str | None]:
    if value is None:
        return (None, None, None)
    label = str(value).split("|", 1)[0]
    parts = [part.strip() for part in label.replace(" ", "").split("~")]
    geonames_id = None
    if parts:
        try:
            geonames_id = int(parts[0])
        except ValueError:
            geonames_id = None
    return (
        geonames_id,
        parts[1] if len(parts) > 1 else None,
        parts[2] if len(parts) > 2 else None,
    )


def _rich_matches(
    response: object, references: list[object]
) -> Iterator[RichGeoNamesEntity]:
    if not isinstance(response, dict):
        return
    for item in response.get("results", []):
        if not isinstance(item, dict):
            continue
        entry = item.get("entry")
        reference_id = item.get("reference")
        if not isinstance(entry, dict) or reference_id is None:
            continue
        try:
            reference = references[int(reference_id) - 1]
        except (ValueError, IndexError):
            continue
        yield _rich_annotation(entry, reference)


def _rich_annotation(entry: dict[str, object], reference: object) -> RichGeoNamesEntity:
    return RichGeoNamesEntity(
        begin=reference.begin,
        end=reference.end,
        id=int(entry["id"]) if entry.get("id") is not None else None,
        name=str(entry["name"]) if entry.get("name") is not None else None,
        latitude=float(entry["latitude"]) if entry.get("latitude") is not None else None,
        longitude=float(entry["longitude"]) if entry.get("longitude") is not None else None,
        featureClass=entry.get("feature_class"),
        featureCode=entry.get("feature_code"),
        countryCode=str(entry["country_code"]) if entry.get("country_code") is not None else None,
        adm1=str(entry["adm1"]) if entry.get("adm1") is not None else None,
        adm2=str(entry["adm2"]) if entry.get("adm2") is not None else None,
        adm3=str(entry["adm3"]) if entry.get("adm3") is not None else None,
        adm4=str(entry["adm4"]) if entry.get("adm4") is not None else None,
        elevation=int(entry["elevation"]) if entry.get("elevation") is not None else None,
        referenceAnnotation={"$ref": reference.ref} if reference.ref is not None else None,
    )


def _entries_by_reference(response: object) -> dict[int, list[dict[str, object]]]:
    out: dict[int, list[dict[str, object]]] = {}
    if not isinstance(response, dict):
        return out
    for item in response.get("results", []):
        if not isinstance(item, dict):
            continue
        entry = item.get("entry")
        reference_id = item.get("reference")
        if not isinstance(entry, dict) or reference_id is None:
            continue
        try:
            index = int(reference_id)
        except (TypeError, ValueError):
            continue
        out.setdefault(index, []).append(entry)
    return out


class GeoNamesAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "duui-geonames-fst/europe migration"}),
        descriptor=AnnotatorDescriptor(
            name="geonames-msgpack-lua",
            version="1.0.0",
            input=IODescriptor(
                annotation=DomainSpec(
                    default=Domain(
                        mimeType="application/x-uima-annotation-spans",
                        languages=["x-unspecified"],
                        types={"NamedEntity": [NAMED_ENTITY_TYPE]},
                    )
                ),
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                )
            ),
            output=IODescriptor(
                types={"GeoNamesEntity": [LEGACY_GEONAMES_TYPE, RICH_GEONAMES_TYPE]},
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemGeoNames.xml",
        parameters_schema={
            "mode": {"type": "string", "default": "find"},
            "max_dist": {"type": "integer", "default": 2},
            "result_selection": {"type": "string", "default": "first"},
            "state_limit": {"type": "integer"},
            "filter": {"type": "string"},
            "timeout": {"type": "number", "default": 120},
            "backend_url": {
                "type": "string",
                "description": "Optional override for a GeoNames FST backend URL. If omitted, the bundled backend is started.",
            },
            "output_type": {
                "type": "string",
                "default": "rich",
                "enum": ["rich"],
                "description": "emits org.texttechnologylab.annotation.geonames.GeoNamesEntity linked to input named-entity spans.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        timeout_seconds = float(
            doc.parameters.get("timeout")
            or doc.parameters.get("timeout_seconds")
            or 120
        )
        annotation_type = str(doc.parameters.get("annotation_type") or NAMED_ENTITY_TYPE)
        annotations = [item for item in doc.fs if item.type == annotation_type]
        if not annotations:
            elapsed_ms = int((time() - started) * 1000)
            await telemetry.count("geonames_matches", 0, output_type="rich")
            await telemetry.timing("geonames_processing_ms", elapsed_ms)
            yield DuuiResult.model_construct(
                annotations=[],
                feature_structures=[],
                meta=None,
                modification_meta=None,
                errors=[],
                sofa=None,
            )
            return

        backend_url = await _resolve_backend_url(doc.parameters)
        request_batch_size = int(doc.parameters.get("request_batch_size") or 4096)
        query_base: dict[str, object] = {
            "mode": doc.parameters.get("mode") or "find",
            "result_selection": doc.parameters.get("result_selection") or "first",
        }
        if doc.parameters.get("filter") is not None:
            query_base["filter"] = doc.parameters["filter"]
        if query_base["mode"] != "find" and doc.parameters.get("max_dist") is not None:
            query_base["max_dist"] = str(doc.parameters["max_dist"])
        if query_base["mode"] == "levenshtein" and doc.parameters.get("state_limit") is not None:
            query_base["state_limit"] = str(doc.parameters["state_limit"])
        await telemetry.info(
            "GeoNames processing started",
            backend_url=backend_url,
            input_annotations=len(annotations),
        )
        matches = 0
        entities: list[RichGeoNamesEntity] = []
        group_started = perf_counter()
        references_by_text: dict[str, list[object]] = {}
        for reference in annotations:
            text = str(reference.features.get("coveredText") or "")
            if text:
                references_by_text.setdefault(text, []).append(reference)
        unique_texts = list(references_by_text)
        group_ms = (perf_counter() - group_started) * 1000.0
        backend_ms = 0.0
        expand_ms = 0.0
        for start in range(0, len(unique_texts), request_batch_size):
            text_batch = unique_texts[start : start + request_batch_size]
            payload = dict(query_base)
            payload["queries"] = [
                {"reference": str(index + 1), "text": text}
                for index, text in enumerate(text_batch)
            ]
            try:
                backend_started = perf_counter()
                response = await asyncio.to_thread(
                    _query_backend, backend_url, payload, timeout_seconds
                )
                backend_ms += (perf_counter() - backend_started) * 1000.0
            except (OSError, URLError, TimeoutError) as exc:
                unavailable(
                    f"GeoNames backend request failed: {exc}", backend_url=backend_url
                )
            except json.JSONDecodeError as exc:
                bad_gateway(
                    f"GeoNames backend returned invalid JSON: {exc}",
                    backend_url=backend_url,
                )
            expand_started = perf_counter()
            entries = _entries_by_reference(response)
            for index, text in enumerate(text_batch, start=1):
                for reference in references_by_text[text]:
                    for entry in entries.get(index, []):
                        matches += 1
                        entities.append(_rich_annotation(entry, reference))
            expand_ms += (perf_counter() - expand_started) * 1000.0
        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count("geonames_matches", matches, output_type="rich")
        await telemetry.count("geonames_unique_queries", len(unique_texts), output_type="rich")
        await telemetry.timing("geonames_group_ms", group_ms)
        await telemetry.timing("geonames_backend_ms", backend_ms)
        await telemetry.timing("geonames_expand_ms", expand_ms)
        await telemetry.timing("geonames_processing_ms", elapsed_ms)
        await telemetry.info(
            "GeoNames processing completed",
            matches=matches,
            elapsed_ms=elapsed_ms,
        )
        yield DuuiResult.model_construct(
            annotations=entities,
            feature_structures=[],
            meta=None,
            modification_meta=None,
            errors=[],
            sofa=None,
        )


app = create_app(GeoNamesAnnotator, request_adapter=AsyncChunkedRequestAdapter())
