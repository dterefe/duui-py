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
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import GeoNamesEntity as LegacyGeoNamesEntity
from duui_py.models.uima_typesystem.texttechnologylab.annotation.geonames.types import GeoNamesEntity as RichGeoNamesEntity

LEGACY_GEONAMES_TYPE = LegacyGeoNamesEntity.model_fields["type"].default
RICH_GEONAMES_TYPE = RichGeoNamesEntity.model_fields["type"].default


def _backend_url(parameters: dict[str, object]) -> str | None:
    value = parameters.get("backend_url") or os.environ.get("GEONAMES_FST_URL")
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


def _first_label(value: object) -> tuple[int | None, str | None, str | None]:
    if value is None:
        return None, None, None
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


def _legacy_matches(response: object) -> list[LegacyGeoNamesEntity]:
    if not isinstance(response, list):
        return []
    annotations: list[LegacyGeoNamesEntity] = []
    for item in response:
        if not isinstance(item, dict):
            continue
        try:
            begin = int(item["begin"])
            end = int(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        geonames_id, mainclass, subclass = _first_label(item.get("match_labels"))
        annotations.append(
            LegacyGeoNamesEntity(
                begin=begin,
                end=end,
                id=geonames_id,
                mainclass=mainclass,
                subclass=subclass,
                features={
                    "match_strings": item.get("match_strings"),
                    "match_labels": item.get("match_labels"),
                },
            )
        )
    return annotations


def _rich_matches(response: object, references: list[object]) -> list[RichGeoNamesEntity]:
    if not isinstance(response, dict):
        return []
    annotations: list[RichGeoNamesEntity] = []
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
        annotations.append(
            RichGeoNamesEntity(
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
        )
    return annotations


class GeoNamesAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "duui-geonames-fst/europe migration"}),
        descriptor=AnnotatorDescriptor(
            name="geonames-msgpack-lua",
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
            "mode": {"type": "string", "default": "levenshtein"},
            "max_dist": {"type": "integer", "default": 2},
            "min_length": {"type": "integer", "default": 5},
            "result_selection": {"type": "string", "default": "first"},
            "max_len": {"type": "integer"},
            "state_limit": {"type": "integer"},
            "filter": {"type": "string"},
            "timeout": {"type": "number", "default": 120},
            "backend_url": {"type": "string"},
            "output_type": {
                "type": "string",
                "default": "legacy",
                "enum": ["legacy", "rich"],
                "description": "legacy emits org.texttechnologylab.annotation.GeoNamesEntity.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        backend_url = _backend_url(doc.parameters)
        output_type = str(doc.parameters.get("output_type") or "legacy")
        timeout_seconds = float(doc.parameters.get("timeout") or doc.parameters.get("timeout_seconds") or 120)
        logger = get_event_logger_or_none()

        if backend_url is None:
            unprocessable("GeoNames backend URL is required via parameter 'backend_url' or GEONAMES_FST_URL.")

        payload: dict[str, object] = {"text": text}
        for key in ("mode", "max_dist", "min_length", "max_len", "state_limit", "result_selection", "filter"):
            if key in doc.parameters:
                payload[key] = doc.parameters[key]

        if logger is not None:
            await logger.info(
                "GeoNames processing started",
                extra={"backend_url": backend_url, "text_length": len(text), "output_type": output_type},
            )

        try:
            response = _query_backend(backend_url, payload, timeout_seconds)
        except (OSError, URLError, TimeoutError) as exc:
            unavailable(f"GeoNames backend request failed: {exc}", backend_url=backend_url)
        except json.JSONDecodeError as exc:
            bad_gateway(f"GeoNames backend returned invalid JSON: {exc}", backend_url=backend_url)

        annotations: list[object]
        if output_type == "rich":
            annotations = _rich_matches(response, [])
        else:
            annotations = _legacy_matches(response)
            if not annotations and isinstance(response, dict):
                bad_gateway("GeoNames backend returned rich response; set output_type=rich or use FST legacy backend.")

        for annotation in annotations:
            yield annotation

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("geonames_matches", len(annotations), output_type=output_type)
        await metrics.timing("geonames_processing_ms", elapsed_ms)

        if logger is not None:
            await logger.info(
                "GeoNames processing completed",
                extra={"matches": len(annotations), "elapsed_ms": elapsed_ms},
            )

        yield AnnotatorMetaData(
            name=self.config.descriptor.name,
            version=self.config.descriptor.version,
            modelName="duui-geonames-fst/europe",
            modelVersion="backend",
        )
        yield DocumentModification(
            user=self.config.descriptor.name,
            timestamp=int(time()),
            comment=f"{self.config.descriptor.name} backend={backend_url}",
        )


app = create_app(GeoNamesAnnotator, request_adapter=AsyncChunkedRequestAdapter())
