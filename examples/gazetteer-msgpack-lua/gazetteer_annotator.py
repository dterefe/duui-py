from __future__ import annotations

from collections.abc import AsyncIterator
from time import time
from urllib.error import URLError
from urllib.request import Request, urlopen

import json
import os

from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import bad_gateway, unavailable, unprocessable
from duui_py.logging import get_event_logger_or_none
from duui_py.metrics import metrics
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
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import Taxon

TAXON_TYPE = Taxon.model_fields["type"].default


def _backend_url(parameters: dict[str, object]) -> str | None:
    value = parameters.get("backend_url") or os.environ.get("GAZETTEER_RS_URL")
    if value is None:
        return None
    value = str(value).strip()
    return value.rstrip("/") if value else None


def _query_backend(backend_url: str, payload: dict[str, object], timeout_seconds: float) -> object:
    request = Request(
        backend_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _matches(response: object) -> list[Taxon]:
    if not isinstance(response, list):
        bad_gateway("Gazetteer backend returned an unexpected JSON root.", json_type=type(response).__name__)
    annotations: list[Taxon] = []
    for item in response:
        if not isinstance(item, dict):
            continue
        try:
            begin = int(item["begin"])
            end = int(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        value = item.get("match_strings")
        identifier = item.get("match_labels")
        annotations.append(
            Taxon(
                begin=begin,
                end=end,
                value=str(value) if value is not None else None,
                identifier=str(identifier) if identifier is not None else None,
                features={
                    "match_strings": value,
                    "match_labels": identifier,
                },
            )
        )
    return annotations


class GazetteerAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/gazetteer-rs/variants/biofid migration"}),
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
                "description": "URL of a running gazetteer-rs/biofid-compatible backend.",
            },
            "timeout": {
                "type": "number",
                "default": 120,
            },
            "max_len": {
                "type": "integer",
            },
            "result_selection": {
                "type": "string",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        backend_url = _backend_url(doc.parameters)
        timeout_seconds = float(doc.parameters.get("timeout") or doc.parameters.get("timeout_seconds") or 120)
        logger = get_event_logger_or_none()

        if backend_url is None:
            unprocessable("Gazetteer backend URL is required via parameter 'backend_url' or GAZETTEER_RS_URL.")

        payload: dict[str, object] = {"text": text}
        for key in ("max_len", "result_selection"):
            if key in doc.parameters:
                payload[key] = doc.parameters[key]

        if logger is not None:
            await logger.info(
                "Gazetteer processing started",
                extra={"backend_url": backend_url, "text_length": len(text)},
            )

        try:
            response = _query_backend(backend_url, payload, timeout_seconds)
        except (OSError, URLError, TimeoutError) as exc:
            unavailable(f"Gazetteer backend request failed: {exc}", backend_url=backend_url)
        except json.JSONDecodeError as exc:
            bad_gateway(f"Gazetteer backend returned invalid JSON: {exc}", backend_url=backend_url)

        annotations = _matches(response)
        for annotation in annotations:
            yield annotation

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("gazetteer_matches", len(annotations))
        await metrics.timing("gazetteer_processing_ms", elapsed_ms)

        if logger is not None:
            await logger.info(
                "Gazetteer processing completed",
                extra={"matches": len(annotations), "elapsed_ms": elapsed_ms},
            )

        yield AnnotatorMetaData(
            name=self.config.descriptor.name,
            version=self.config.descriptor.version,
            modelName="gazetteer-rs/biofid",
            modelVersion="1.5.4",
        )
        yield DocumentModification(
            user=self.config.descriptor.name,
            timestamp=int(time()),
            comment=f"{self.config.descriptor.name} backend={backend_url}",
        )


app = create_app(GazetteerAnnotator, request_adapter=AsyncChunkedRequestAdapter())
