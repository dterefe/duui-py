from __future__ import annotations

import asyncio
import atexit
import json
import logging
import subprocess
import threading
from collections.abc import AsyncIterator
from time import sleep, time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import bad_gateway, timeout, unavailable
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    AnnotatorMetaData,
    DocumentModification,
    Domain,
    DomainSpec,
    IODescriptor,
    V1RequestEnvelope,
)
from duui_py.models.uima import sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.biofid.gnfinder.types import (
    GNFinderMetaData,
)
from duui_py.telemetry import telemetry

from gnfinder_annotator import _name_to_taxon, _resolve_binary, _to_bool, _to_int

logger = logging.getLogger(__name__)

DEFAULT_GNFINDER_API_PORT = 18999
_BACKEND_LOCK = threading.Lock()
_BACKEND_PROCESS: subprocess.Popen[bytes] | None = None


def _backend_url(parameters: dict[str, object]) -> str:
    value = parameters.get("backend_url")
    if value is None or not str(value).strip():
        value = _ensure_local_backend()
    value = str(value).strip().rstrip("/")
    if value.endswith("/api/v1/find"):
        return value
    return value + "/api/v1/find"


def _ensure_local_backend() -> str:
    def _ensure_local_backend() -> str:
        global _BACKEND_PROCESS
        port = DEFAULT_GNFINDER_API_PORT
        url = f"http://127.0.0.1:{port}"
        if _backend_ready(url):
            logger.debug("Local GNFinder REST backend already ready: %s", url)
            return url
        with _BACKEND_LOCK:
            if _backend_ready(url):
                logger.debug("Local GNFinder REST backend became ready under lock: %s", url)
                return url
            if _BACKEND_PROCESS is None or _BACKEND_PROCESS.poll() is not None:
                binary = _resolve_binary()
                if binary is None:
                    logger.error("No bundled GNFinder binary found for REST backend")
                    unavailable(
                        "No bundled GNFinder binary found.",
                        path="duui-uima/duui-GNFinder/gnfinder",
                    )
                logger.info("Starting local GNFinder REST backend: binary=%s port=%d", binary, port)
                _BACKEND_PROCESS = subprocess.Popen(
                    [binary, "-p", str(port)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                atexit.register(_stop_local_backend)
            deadline = time() + 20
            while time() < deadline:
                if _backend_ready(url):
                    logger.info("Local GNFinder REST backend ready: %s", url)
                    return url
                sleep(0.25)
        logger.error("Local GNFinder REST backend did not become ready: %s", url)
        unavailable("Bundled GNFinder REST backend did not become ready.", backend_url=url)

def _stop_local_backend() -> None:
    if _BACKEND_PROCESS is not None and _BACKEND_PROCESS.poll() is None:
        _BACKEND_PROCESS.terminate()


def _backend_ready(url: str) -> bool:
    try:
        with urlopen(url.rstrip("/") + "/api/v1/ping", timeout=1) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def _sources(value: object | None) -> list[int]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw = value
    else:
        raw = str(value).split(",")
    out: list[int] = []
    for item in raw:
        try:
            out.append(int(str(item).strip()))
        except ValueError:
            continue
    return out


def _query_backend(
    backend_url: str, payload: dict[str, object], timeout_seconds: float
) -> dict[str, object]:
    request = Request(
        backend_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            parsed = json.loads(response.read().decode("utf-8"))
            logger.debug("GNFinder REST backend responded successfully: %s", backend_url)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        logger.error(
            "GNFinder REST backend HTTP error: status=%s detail=%s url=%s",
            exc.code, detail, backend_url,
        )
        bad_gateway(
            "GNFinder REST backend returned an error.",
            status=exc.code,
            detail=detail,
            backend_url=backend_url,
        )
    except (OSError, URLError, TimeoutError) as exc:
        logger.error(
            "GNFinder REST backend request failed: %s url=%s", exc, backend_url,
        )
        bad_gateway(
            f"GNFinder REST backend request failed: {exc}",
            backend_url=backend_url,
        )
    except json.JSONDecodeError as exc:
        logger.error(
            "GNFinder REST backend returned invalid JSON: %s url=%s", exc, backend_url,
        )
        bad_gateway(
            "GNFinder REST backend returned invalid JSON.",
            error=str(exc),
            backend_url=backend_url,
        )
    if not isinstance(parsed, dict):
        logger.error(
            "GNFinder REST backend unexpected root type: %s url=%s",
            type(parsed).__name__, backend_url,
        )
        bad_gateway(
            "GNFinder REST backend returned an unexpected JSON root.",
            json_type=type(parsed).__name__,
            backend_url=backend_url,
        )
    return parsed


class GNFinderRestAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(
            meta={
                "example": "duui-gnfinder REST migration",
                "source": "GNFinder documented /api/v1/find backend",
            }
        ),
        descriptor=AnnotatorDescriptor(
            name="gnfinder-rest-msgpack-lua",
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
            "backend_url": {
                "type": "string",
                "description": "Optional override for a GNFinder REST server base URL. If omitted, the bundled GNFinder backend is started.",
            },
            "timeout_seconds": {"type": "number", "default": 120},
            "lang": {
                "type": "string",
                "default": "detect",
                "description": "GNFinder API language value: eng, deu, detect, or empty.",
            },
            "verify": {"type": "boolean", "default": True},
            "sources": {
                "type": "string",
                "description": "Comma-separated GNFinder verification data-source ids.",
            },
            "all_matches": {"type": "boolean", "default": False},
            "unique_names": {"type": "boolean", "default": False},
            "ambiguous_uninomials": {"type": "boolean", "default": False},
            "no_bayes": {"type": "boolean", "default": False},
            "odds_details": {"type": "boolean", "default": False},
            "words_around": {"type": "integer"},
            "return_content": {"type": "boolean", "default": False},
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        backend_url = _backend_url(doc.parameters)
        timeout_seconds = float(doc.parameters.get("timeout_seconds") or 120)
        logger.info(
            "GNFinder REST processing started: text_length=%d backend=%s timeout=%s",
            len(text), backend_url, timeout_seconds,
        )
        verify = _to_bool(doc.parameters.get("verify"), True)
        sources = _sources(doc.parameters.get("sources"))
        all_matches = _to_bool(doc.parameters.get("all_matches"))
        payload: dict[str, object] = {
            "text": text,
            "format": "compact",
            "verification": verify,
            "language": str(doc.parameters.get("lang") or "detect"),
            "sources": sources,
            "withAllMatches": all_matches,
            "unique": _to_bool(doc.parameters.get("unique_names")),
            "ambiguousNames": _to_bool(doc.parameters.get("ambiguous_uninomials")),
            "noBayes": _to_bool(doc.parameters.get("no_bayes")),
            "oddsDetails": _to_bool(doc.parameters.get("odds_details")),
            "returnContent": _to_bool(doc.parameters.get("return_content")),
        }
        words_around = _to_int(doc.parameters.get("words_around"))
        if words_around is not None:
            payload["wordsAround"] = words_around
        await telemetry.info(
            "GNFinder REST processing started",
            backend_url=backend_url,
            text_length=len(text),
            verify=verify,
            sources=sources,
            all_matches=all_matches,
        )
        try:
            result = await asyncio.to_thread(
                _query_backend, backend_url, payload, timeout_seconds
            )
        except TimeoutError:
            logger.error(
                "GNFinder REST backend timed out: timeout=%s url=%s",
                timeout_seconds, backend_url,
            )
            timeout(
                "GNFinder REST backend timed out",
                timeout_seconds=timeout_seconds,
                backend_url=backend_url,
            )
        matches = 0
        names = result.get("names", [])
        if not isinstance(names, list):
            bad_gateway(
                "GNFinder REST result has invalid names field",
                field_type=type(names).__name__,
            )
        for name in names:
            if not isinstance(name, dict):
                continue
            matches += 1
            yield _name_to_taxon(name, verify=verify)
        logger.info(
            "GNFinder REST extracted %d taxon annotations out of %d names",
            matches, len(names),
        )
        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count(
            "gnfinder_rest_taxon_matches",
            matches,
            verify=str(verify).lower(),
            all_matches=str(all_matches).lower(),
        )
        await telemetry.timing("gnfinder_rest_processing_ms", elapsed_ms)
        metadata = result.get("metadata", {})
        if isinstance(metadata, dict):
            yield GNFinderMetaData(
                date=(
                    str(metadata.get("date"))
                    if metadata.get("date") is not None
                    else None
                ),
                language=(
                    str(metadata.get("language"))
                    if metadata.get("language") is not None
                    else None
                ),
                version=(
                    str(metadata.get("gnfinderVersion"))
                    if metadata.get("gnfinderVersion") is not None
                    else None
                ),
            )
        await telemetry.info(
            "GNFinder REST processing completed",
            matches=matches,
            elapsed_ms=elapsed_ms,
        )
        logger.info(
            "GNFinder REST processing completed: matches=%d elapsed_ms=%d",
            matches, elapsed_ms,
        )
        yield AnnotatorMetaData(
            name=self.config.descriptor.name,
            version=self.config.descriptor.version,
            modelName="gnfinder-rest",
            modelVersion=(
                str(metadata.get("gnfinderVersion"))
                if isinstance(metadata, dict)
                and metadata.get("gnfinderVersion") is not None
                else None
            ),
        )
        yield DocumentModification(
            user=self.config.descriptor.name,
            timestamp=int(time()),
            comment=f"{self.config.descriptor.name} backend={backend_url}",
        )


app = create_app(GNFinderRestAnnotator, request_adapter=AsyncChunkedRequestAdapter())
