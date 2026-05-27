from __future__ import annotations
from functools import lru_cache
from time import time
from typing import Any
import os
import json
from pathlib import Path
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

TAXONERD_MODELS = {
    "biobert": "en_ner_eco_biobert",
    "en_ner_eco_biobert": "en_ner_eco_biobert",
    "biobert_weak": "en_ner_eco_biobert_weak",
    "en_ner_eco_biobert_weak": "en_ner_eco_biobert_weak",
    "md": "en_ner_eco_md",
    "en_ner_eco_md": "en_ner_eco_md",
    "md_weak": "en_ner_eco_md_weak",
    "en_ner_eco_md_weak": "en_ner_eco_md_weak",
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


class TextImagerRequest(BaseModel):
    text: str
    linking: str = "gbif_backbone"
    threshold: float = 0.7
    exclude: list[str] = Field(
        default_factory=lambda: [
            "tagger",
            "parser",
            "taxo_abbrev_detector",
            "taxon_linker",
            "pysbd_sentencizer",
        ]
    )
    model: str = "en_ner_eco_md"


def _model_name(value: str | None) -> str:
    value = value or os.environ.get("TEXTIMAGER_TAXONERD_MODEL_NAME") or "en_ner_eco_md"
    return TAXONERD_MODELS.get(value, value)


def _linker_name(value: str | None) -> str | None:
    value = value or os.environ.get("TEXTIMAGER_TAXONERD_LINKER_NAME") or "gbif_backbone"
    return TAXONERD_LINKERS.get(value, value)


@lru_cache(maxsize=3)
def _load_taxonerd(
    model: str, linker: str | None, threshold: float, exclude: tuple[str, ...]
):
    try:
        from taxonerd import TaxoNERD
    except Exception as exc:
        unavailable(
            "TaxoNERD is not installed in this runtime.", exception=type(exc).__name__
        )
    try:
        taxonerd = TaxoNERD(prefer_gpu=False)
        taxonerd.load(
            model=model,
            exclude=list(exclude),
            linker=linker,
            threshold=threshold,
        )
        return taxonerd
    except Exception as exc:
        unavailable(
            "TaxoNERD model could not be loaded.",
            model=model,
            linker=linker,
            threshold=threshold,
            exclude=list(exclude),
            exception=type(exc).__name__,
        )


def _links(value: object) -> list[object]:
    if not isinstance(value, list) or not value:
        return []
    first = value[0]
    if isinstance(first, (list, tuple)):
        return list(first[:3])
    return list(value[:3])


def _taxon_row_to_legacy(row: list[object], ind: int) -> dict[str, object]:
    if len(row) < 2:
        bad_gateway("TaxoNERD returned a malformed row.", row=str(row))
    marker = str(row[0]).split()
    if len(marker) < 3:
        bad_gateway("TaxoNERD returned a malformed span marker.", marker=str(row[0]))
    links = _links(row[2]) if len(row) > 2 else []
    while len(links) < 3:
        links.append("")
    return {
        "ind": ind,
        "begin": int(marker[1]),
        "end": int(marker[2]),
        "unknown": marker[0],
        "text": str(row[1]),
        "link": links,
        "comment": [
            {"id": str(links[0]), "value": str(links[1]), "propability": links[2]}
        ]
        if any(links)
        else [],
        "write_token": True,
    }


class TaxoNERDLegacyAnnotator(DuuiAnnotator[TextImagerRequest, dict[str, object]]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/taxoNERD legacy Lua migration"}),
        descriptor=AnnotatorDescriptor(
            name="taxonerd-legacy-lua",
            version="1.3.3",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="application/json", languages=["x-unspecified"]
                    )
                )
            ),
            output=IODescriptor(
                types={
                    "Taxon": ["org.texttechnologylab.annotation.type.Taxon"],
                    "AnnotationComment": [
                        "org.texttechnologylab.annotation.AnnotationComment"
                    ],
                },
                text=DomainSpec(
                    default=Domain(
                        mimeType="application/json", languages=["x-unspecified"]
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemTaxoNERDLegacy.xml",
        parameters_schema={
            "model": {
                "type": "string",
                "default": "en_ner_eco_md",
                "description": "Legacy TaxoNERD model.",
            },
            "linking": {
                "type": "string",
                "default": "gbif_backbone",
                "description": "Legacy TaxoNERD linker.",
            },
            "threshold": {
                "type": "number",
                "default": 0.7,
                "description": "Legacy TaxoNERD linking threshold.",
            },
            "exclude": {
                "type": "array",
                "description": "Legacy TaxoNERD pipeline components to exclude.",
            },
        },
    )

    def codec(self):
        return LuaCustomCodec(
            (Path(__file__).resolve().parent / "communication.lua").read_text(
                encoding="utf-8"
            ),
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=lambda body: TextImagerRequest.model_validate_json(body),
            encode_response=lambda result: json.dumps(
                result, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8"),
            name="taxonerd-legacy-lua",
        )

    @telemetry.timed("taxonerd_legacy_processing_ms", annotator="taxonerd-legacy")
    async def process(self, doc: TextImagerRequest) -> dict[str, object]:
        started = time()
        model = _model_name(doc.model)
        linker = _linker_name(doc.linking)
        threshold = float(doc.threshold)
        exclude = tuple(doc.exclude)
        name = os.environ.get(
            "TEXTIMAGER_TAXONERD_ANNOTATOR_NAME", "textimager-duui-taxonerd"
        )
        version = os.environ.get("TEXTIMAGER_TAXONERD_ANNOTATOR_VERSION", "1.3.3")
        model_version = os.environ.get("TEXTIMAGER_TAXONERD_MODEL_VERSION", "1.0.0")
        await telemetry.trace(
            "TaxoNERD legacy processing started",
            model=model,
            linker=linker,
            threshold=threshold,
            exclude=list(exclude),
        )
        taxo = _load_taxonerd(model, linker, threshold, exclude)
        try:
            rows = taxo.find_in_text(doc.text).values.tolist()
        except Exception as exc:
            await telemetry.error(
                "TaxoNERD legacy model request failed",
                model=model,
                linker=linker or "none",
                exception=type(exc).__name__,
            )
            bad_gateway(
                "TaxoNERD processing failed.",
                exception=type(exc).__name__,
                detail=str(exc),
            )
        taxons = [_taxon_row_to_legacy(row, ind) for ind, row in enumerate(rows)]
        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count("taxonerd_legacy_taxons", len(taxons), model=model)
        await telemetry.debug(
            "TaxoNERD legacy processing completed",
            taxons=len(taxons),
            elapsed_ms=elapsed_ms,
        )
        return {
            "taxons": taxons,
            "meta": {
                "name": name,
                "version": version,
                "modelName": model,
                "modelVersion": model_version,
                "linkerName": linker,
            },
            "modification_meta": {
                "user": name,
                "timestamp": int(time()),
                "comment": f"{name} ({version})",
            },
        }


app = create_app(TaxoNERDLegacyAnnotator)
