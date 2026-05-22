from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from time import time
from typing import Any

import asyncio
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

TAXONERD_MODELS = {
    "biobert": "en_ner_eco_biobert",
    "md": "en_ner_eco_md",
    "en_ner_eco_biobert": "en_ner_eco_biobert",
    "en_ner_eco_md": "en_ner_eco_md",
}

TAXONERD_LINKERS = {
    "gbif": "gbif_backbone",
    "gbif_backbone": "gbif_backbone",
    "taxref": "taxref",
    "ncbi": "ncbi_taxonomy",
    "ncbi_taxonomy": "ncbi_taxonomy",
    "ncbi_lite": "ncbi_taxonomy_lite",
    "ncbi_taxonomy_lite": "ncbi_taxonomy_lite",
    "none": None,
    "": None,
}


def _parameter(parameters: dict[str, object], *names: str, default: object = None) -> object:
    for name in names:
        value = parameters.get(name)
        if value is not None:
            return value
    return default


def _model_name(value: object | None) -> str:
    configured = str(value or os.environ.get("TAXONERD_MODEL") or "en_ner_eco_md")
    model = TAXONERD_MODELS.get(configured)
    if model is None:
        unprocessable("Unsupported TaxoNERD model.", model=configured, supported=sorted(TAXONERD_MODELS))
    return model


def _linker_name(value: object | None) -> str | None:
    configured = str(value if value is not None else os.environ.get("TAXONERD_LINKING", "gbif_backbone"))
    if configured not in TAXONERD_LINKERS:
        unprocessable("Unsupported TaxoNERD linker.", linker=configured, supported=sorted(TAXONERD_LINKERS))
    return TAXONERD_LINKERS[configured]


def _bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _offsets(value: object, text: str, mention: str) -> tuple[int, int] | None:
    if isinstance(value, str):
        parts = value.split()
        ints = []
        for part in parts:
            try:
                ints.append(int(part))
            except ValueError:
                continue
        if len(ints) >= 2:
            return ints[-2], ints[-1]
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return int(value[0]), int(value[1])
        except (TypeError, ValueError):
            pass
    if mention:
        begin = text.find(mention)
        if begin >= 0:
            return begin, begin + len(mention)
    return None


def _links(entity: object) -> list[dict[str, object]]:
    if entity is None:
        return []
    if isinstance(entity, list):
        values = entity
    else:
        values = [entity]
    links = []
    for value in values:
        if isinstance(value, dict):
            links.append(value)
            continue
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            item = {
                "id": str(value[0]),
                "value": str(value[1]),
            }
            if len(value) >= 3:
                try:
                    item["probability"] = float(value[2])
                except (TypeError, ValueError):
                    item["probability"] = value[2]
            links.append(item)
    return links


@lru_cache(maxsize=4)
def _load_taxonerd(model: str, linker: str | None, prefer_gpu: bool, with_abbrev: bool):
    try:
        from taxonerd import TaxoNERD
    except Exception as exc:  # noqa: BLE001
        unavailable("TaxoNERD is not installed in this runtime.", exception=type(exc).__name__)

    kwargs: dict[str, Any] = {
        "prefer_gpu": prefer_gpu,
        "with_abbrev": with_abbrev,
        "model": model,
        "verbose": True,
    }
    if linker:
        kwargs["with_linking"] = linker
    return TaxoNERD(**kwargs)


def _find_taxa(text: str, model: str, linker: str | None, prefer_gpu: bool, with_abbrev: bool) -> list[Taxon]:
    taxonerd = _load_taxonerd(model, linker, prefer_gpu, with_abbrev)
    table = taxonerd.find_in_text(text)
    rows = table.to_dict("records") if hasattr(table, "to_dict") else []
    annotations: list[Taxon] = []
    for row in rows:
        mention = str(row.get("mention") or row.get("text") or row.get("name") or row.get("entity_text") or "")
        if not mention and row.get("entity") is not None:
            mention = str(row.get("entity"))
        offsets = _offsets(row.get("offsets"), text, mention)
        if offsets is None:
            bad_gateway("TaxoNERD returned a row without usable offsets.", row=row)
        begin, end = offsets
        links = _links(row.get("entity"))
        identifier = links[0]["id"] if links else None
        annotations.append(
            Taxon(
                begin=begin,
                end=end,
                value=text[begin:end] if text and 0 <= begin <= end <= len(text) else mention,
                identifier=str(identifier) if identifier is not None else None,
                features={
                    "linker": linker,
                    "model": model,
                    "links": links,
                    "taxonerd": {str(k): v for k, v in row.items() if k not in {"offsets", "entity"}},
                },
            )
        )
    return annotations


class TaxoNERDAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/taxoNERD migration"}),
        descriptor=AnnotatorDescriptor(
            name="taxonerd-msgpack-lua",
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
                types={"Taxon": ["org.texttechnologylab.annotation.type.Taxon"]},
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemTaxoNERD.xml",
        parameters_schema={
            "model": {
                "type": "string",
                "default": "en_ner_eco_md",
                "description": "Legacy-compatible TaxoNERD model alias or package name.",
            },
            "model_name": {
                "type": "string",
                "description": "Legacy parameter alias for model.",
            },
            "linking": {
                "type": "string",
                "default": "gbif_backbone",
                "description": "TaxoNERD linker alias or package name.",
            },
            "linker_name": {
                "type": "string",
                "description": "Legacy parameter alias for linking.",
            },
            "prefer_gpu": {
                "type": "boolean",
                "default": False,
                "description": "Passed to TaxoNERD.",
            },
            "with_abbrev": {
                "type": "boolean",
                "default": True,
                "description": "Passed to TaxoNERD.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        model = _model_name(_parameter(doc.parameters, "model", "model_name"))
        linker = _linker_name(_parameter(doc.parameters, "linking", "linker_name"))
        prefer_gpu = _bool(_parameter(doc.parameters, "prefer_gpu", default=False), False)
        with_abbrev = _bool(_parameter(doc.parameters, "with_abbrev", default=True), True)
        logger = get_event_logger_or_none()

        if logger is not None:
            await logger.info(
                "TaxoNERD processing started",
                extra={"model": model, "linker": linker, "text_length": len(text)},
            )

        annotations = await asyncio.to_thread(_find_taxa, text, model, linker, prefer_gpu, with_abbrev)
        for annotation in annotations:
            yield annotation

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("taxonerd_taxon_matches", len(annotations), linking=linker or "none", model=model)
        await metrics.timing("taxonerd_processing_ms", elapsed_ms)

        if logger is not None:
            await logger.info(
                "TaxoNERD processing completed",
                extra={"matches": len(annotations), "elapsed_ms": elapsed_ms},
            )

        yield AnnotatorMetaData(
            name=self.config.descriptor.name,
            version=self.config.descriptor.version,
            modelName=model,
            modelVersion="1.0.0",
        )
        yield DocumentModification(
            user=self.config.descriptor.name,
            timestamp=int(time()),
            comment=f"{self.config.descriptor.name} TaxoNERD model={model} linker={linker or 'none'}",
        )


app = create_app(TaxoNERDAnnotator, request_adapter=AsyncChunkedRequestAdapter())
