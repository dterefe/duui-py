from __future__ import annotations

from collections.abc import AsyncIterator

import json
import os
from time import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import bad_gateway, unavailable, unprocessable
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
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.ner.type.types import Location
from duui_py.models.uima_typesystem.texttechnologylab.annotation.geonames.types import GeoNamesEntity

LOCATION_TYPE = Location.model_fields["type"].default
GEONAMES_TYPE = GeoNamesEntity.model_fields["type"].default


class GeoNamesAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "duui-geonames-fst migration"}),
        descriptor=AnnotatorDescriptor(
            name="geonames-msgpack-lua",
            version="1.0.0",
            input=IODescriptor(
                types={"Location": [LOCATION_TYPE]},
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                        types={"Span": [LOCATION_TYPE]},
                    )
                ),
                annotation=DomainSpec(
                    default=Domain(
                        mimeType="application/x-uima-annotation-spans",
                        languages=["x-unspecified"],
                        types={"Span": [LOCATION_TYPE]},
                    )
                ),
            ),
            output=IODescriptor(
                types={"GeoNamesEntity": [GEONAMES_TYPE]},
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
            "annotation_type": {
                "type": "string",
                "default": LOCATION_TYPE,
                "description": "Input annotation type containing place mentions.",
            },
            "mode": {
                "type": "string",
                "default": "find",
                "enum": ["find", "levenshtein"],
                "description": "Match mode compatible with duui-geonames-fst.",
            },
            "result_selection": {
                "type": "string",
                "default": "first",
                "description": "Result selection mode compatible with duui-geonames-fst.",
            },
            "max_dist": {
                "type": "integer",
                "default": 2,
                "description": "Maximum edit distance for levenshtein mode.",
            },
            "state_limit": {
                "type": "integer",
                "default": 10000,
                "description": "State limit for levenshtein mode.",
            },
            "filter": {
                "type": "string",
                "description": "Optional GeoNames filter expression.",
            },
            "backend_url": {
                "type": "string",
                "description": "URL of a running duui-geonames-fst-compatible HTTP backend.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @staticmethod
    def _is_type(value: str, target: str) -> bool:
        return value == target or value.endswith(f".{target.split('.')[-1]}")

    @staticmethod
    def _backend_url(parameters: dict[str, object]) -> str | None:
        value = parameters.get("backend_url") or os.environ.get("GEONAMES_FST_URL")
        if value is None:
            return None
        value = str(value).strip()
        return value.rstrip("/") if value else None

    @staticmethod
    def _query_backend(backend_url: str, payload: dict[str, object]) -> dict[str, object]:
        request = Request(
            backend_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=120) as response:
            decoded = json.loads(response.read().decode("utf-8"))
        if not isinstance(decoded, dict):
            bad_gateway("GeoNames backend returned a non-object JSON response", backend_url=backend_url)
        return decoded

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        annotation_type = str(doc.parameters.get("annotation_type") or LOCATION_TYPE)
        mode = str(doc.parameters.get("mode") or "find")
        result_selection = str(doc.parameters.get("result_selection") or "first")
        backend_url = self._backend_url(doc.parameters)
        locations = [
            fs
            for fs in doc.fs
            if fs.begin is not None
            and fs.end is not None
            and fs.end > fs.begin
            and self._is_type(fs.type, annotation_type)
        ]

        if backend_url is None:
            unprocessable(
                "GeoNames backend URL is required via parameter 'backend_url' or GEONAMES_FST_URL.",
                parameter="backend_url",
            )

        queries = []
        references = []
        for index, location in enumerate(locations, 1):
            references.append(location)
            queries.append(
                {
                    "reference": str(index),
                    "text": text[location.begin : location.end] if text else str(location.features.get("value") or ""),
                }
            )

        payload: dict[str, object] = {
            "mode": mode,
            "result_selection": result_selection,
            "queries": queries,
        }
        for key in ("filter", "max_dist", "state_limit"):
            if key in doc.parameters:
                payload[key] = str(doc.parameters[key])

        try:
            response = self._query_backend(backend_url, payload)
        except (OSError, URLError, TimeoutError) as exc:
            unavailable(f"GeoNames backend request failed: {exc}", backend_url=backend_url)
        except json.JSONDecodeError as exc:
            bad_gateway(f"GeoNames backend returned invalid JSON: {exc}", backend_url=backend_url)

        matches = 0
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

            matches += 1
            yield GeoNamesEntity(
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

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("geonames_locations_received", len(locations), mode=mode, result_selection=result_selection)
        await metrics.count("geonames_matches", matches, mode=mode, result_selection=result_selection)
        await metrics.timing("geonames_processing_ms", elapsed_ms)

        yield AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName="duui-geonames-fst",
                modelVersion="backend",
        )
        yield DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} GeoNames FST backend lookup",
        )


app = create_app(GeoNamesAnnotator, request_adapter=AsyncChunkedRequestAdapter())
