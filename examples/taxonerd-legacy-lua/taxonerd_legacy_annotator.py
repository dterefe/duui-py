from __future__ import annotations

from functools import lru_cache
from time import time
from typing import Any

import os
import json
from pathlib import Path

from pydantic import BaseModel

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.lua_custom import LuaCustomCodec
from duui_py.errors import bad_gateway, unavailable
from duui_py.logging import get_event_logger_or_none
from duui_py.metrics import metrics
from duui_py.models import AnnotatorConfig, AnnotatorDescriptor, AnnotatorMeta, Domain, DomainSpec, IODescriptor


TAXONERD_MODELS = {
    "biobert": "en_ner_eco_biobert",
    "en_ner_eco_biobert": "en_ner_eco_biobert",
    "md": "en_ner_eco_md",
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


class TextImagerRequest(BaseModel):
    text: str


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _model_name() -> str:
    value = _env("TEXTIMAGER_TAXONERD_MODEL_NAME", "biobert")
    return TAXONERD_MODELS.get(value, value)


def _linker_name() -> str | None:
    value = _env("TEXTIMAGER_TAXONERD_LINKER_NAME", "taxref")
    return TAXONERD_LINKERS.get(value, value)


@lru_cache(maxsize=3)
def _load_taxonerd(model: str, linker: str | None):
    try:
        from taxonerd import TaxoNERD
    except Exception as exc:  # noqa: BLE001
        unavailable("TaxoNERD is not installed in this runtime.", exception=type(exc).__name__)
    try:
        return TaxoNERD(prefer_gpu=False, with_abbrev=True, model=model, with_linking=linker, verbose=True)
    except Exception as exc:  # noqa: BLE001
        unavailable("TaxoNERD model could not be loaded.", model=model, linker=linker, exception=type(exc).__name__)


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
        "write_token": True,
    }


class TaxoNERDLegacyAnnotator(DuuiAnnotator[TextImagerRequest, dict[str, object]]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/taxoNERD legacy Lua migration"}),
        descriptor=AnnotatorDescriptor(
            name="taxonerd-legacy-lua",
            version="1.3.3",
            input=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json", languages=["x-unspecified"]))),
            output=IODescriptor(
                types={
                    "Taxon": ["org.texttechnologylab.annotation.type.Taxon"],
                    "AnnotationComment": ["org.texttechnologylab.annotation.AnnotationComment"],
                },
                text=DomainSpec(default=Domain(mimeType="application/json", languages=["x-unspecified"])),
            ),
        ),
        typesystem_xml_path="TypeSystemTaxoNERDLegacy.xml",
        parameters_schema={},
    )

    def codec(self):
        return LuaCustomCodec(
            (Path(__file__).resolve().parent / "communication.lua").read_text(encoding="utf-8"),
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=lambda body: TextImagerRequest.model_validate_json(body),
            encode_response=lambda result: json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            name="taxonerd-legacy-lua",
        )

    async def process(self, doc: TextImagerRequest) -> dict[str, object]:
        started = time()
        model = _model_name()
        linker = _linker_name()
        name = _env("TEXTIMAGER_TAXONERD_ANNOTATOR_NAME", "textimager-duui-taxonerd")
        version = _env("TEXTIMAGER_TAXONERD_ANNOTATOR_VERSION", "1.3.3")
        model_version = _env("TEXTIMAGER_TAXONERD_MODEL_VERSION", "1.0.0")
        logger = get_event_logger_or_none()

        if logger is not None:
            await logger.info("TaxoNERD legacy processing started", extra={"model": model, "linker": linker})

        taxo = _load_taxonerd(model, linker)
        try:
            rows = taxo.find_in_text(doc.text).values.tolist()
        except Exception as exc:  # noqa: BLE001
            bad_gateway("TaxoNERD processing failed.", exception=type(exc).__name__, detail=str(exc))

        taxons = [_taxon_row_to_legacy(row, ind) for ind, row in enumerate(rows)]
        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("taxonerd_legacy_taxons", len(taxons), model=model)
        await metrics.timing("taxonerd_legacy_processing_ms", elapsed_ms)

        if logger is not None:
            await logger.info("TaxoNERD legacy processing completed", extra={"taxons": len(taxons), "elapsed_ms": elapsed_ms})

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
