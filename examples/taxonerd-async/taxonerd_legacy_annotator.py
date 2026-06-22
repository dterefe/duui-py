from __future__ import annotations

import asyncio
import os
from typing import Any

from pydantic import BaseModel, Field

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.lua_custom import LuaCustomCodec
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    Domain,
    DomainSpec,
    IODescriptor,
)
from duui_py.utils.params import resolve_prefer_gpu

from _taxonerd_shared import (
    LINK_ID_FEATURE,
    LINK_SCORE_FEATURE,
    LINK_VALUE_FEATURE,
    load_taxonerd,
    run_legacy_procedure,
)


LEGACY_LUA = r'''
StandardCharsets = luajava.bindClass("java.nio.charset.StandardCharsets")
function serialize(inputCas, outputStream, params)
    params = params or {}
    outputStream:write(json.encode({
        text = inputCas:getDocumentText(),
        linking = params.linking or "gbif_backbone",
        threshold = tonumber(params.threshold) or 0.7,
        exclude = {'tagger','parser','taxo_abbrev_detector','taxon_linker','pysbd_sentencizer'},
        model = params.model or "en_ner_eco_md",
        prefer_gpu = params.prefer_gpu == "true",
    }))
end
function deserialize(inputCas, inputStream)
    local inputString = luajava.newInstance("java.lang.String", inputStream:readAllBytes(), StandardCharsets.UTF_8)
    local results = json.decode(inputString)
    for _, tax in ipairs(results.taxons or {}) do
        local taxon = luajava.newInstance("org.texttechnologylab.annotation.type.Taxon", inputCas)
        taxon:setBegin(tax.begin)
        taxon:setEnd(tax["end"])
        taxon:addToIndexes()
        for _, comment in ipairs(tax.comment or {}) do
            local cID = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
            cID:setKey("linking")
            cID:setValue(comment.id)
            cID:setReference(taxon)
            cID:addToIndexes()

            local cValue = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
            cValue:setKey("value")
            cValue:setValue(comment.value)
            cValue:setReference(cID)
            cValue:addToIndexes()

            local cPropability = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
            cPropability:setKey("propability")
            cPropability:setValue(comment.propability)
            cPropability:setReference(cID)
            cPropability:addToIndexes()
        end
    end
end
'''


class GBIFComment(BaseModel):
    id: str
    value: str
    propability: float


class TaxonLegacyOut(BaseModel):
    begin: int
    end: int
    comment: list[GBIFComment] = Field(default_factory=list)


class TaxoNERDLegacyRequest(BaseModel):
    text: str
    linking: str = "gbif_backbone"
    threshold: float = 0.7
    exclude: list[str] = Field(default_factory=lambda: [
        "tagger", "parser", "taxo_abbrev_detector", "taxon_linker", "pysbd_sentencizer",
    ])
    model: str = "en_ner_eco_md"
    prefer_gpu: bool = False


class TaxoNERDLegacyResponse(BaseModel):
    taxons: list[TaxonLegacyOut]


class TaxoNERDLegacyAnnotator(
    DuuiAnnotator[TaxoNERDLegacyRequest, TaxoNERDLegacyResponse]
):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "abrami TaxoNERD legacy Lua JSON"}),
        descriptor=AnnotatorDescriptor(
            name="taxonerd-legacy-lua-json",
            version="1.0.0",
            input=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json"))),
            output=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json"))),
        ),
        typesystem_xml_path="TypeSystemTaxoNERD.xml",
        parameters_schema={
            "model": {"type": "string", "default": "en_ner_eco_md", "description": "TaxoNERD model alias."},
            "linking": {"type": "string", "default": "gbif_backbone", "description": "TaxoNERD linker alias."},
            "threshold": {"type": "number", "default": 0.7},
            "exclude": {"type": "array", "default": ["tagger", "parser", "taxo_abbrev_detector", "taxon_linker", "pysbd_sentencizer"]},
            "prefer_gpu": {"type": "boolean", "default": False},
        },
    )

    def codec(self) -> LuaCustomCodec[TaxoNERDLegacyRequest, TaxoNERDLegacyResponse]:
        return LuaCustomCodec(
            LEGACY_LUA,
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=TaxoNERDLegacyRequest.model_validate_json,
            encode_response=lambda result: result.model_dump_json(by_alias=True).encode("utf-8"),
            name="taxonerd-legacy-lua-json",
        )

    async def startup(self) -> None:
        exclude_raw = os.getenv("DUUI_TAXONERD_PRELOAD_EXCLUDE", "")
        exclude = (
            tuple(item.strip() for item in exclude_raw.split(",") if item.strip())
            if exclude_raw.strip()
            else ("tagger", "parser", "taxo_abbrev_detector", "taxon_linker", "pysbd_sentencizer")
        )
        model = os.getenv("DUUI_TAXONERD_PRELOAD_MODEL", "en_ner_eco_md")
        linker = os.getenv("DUUI_TAXONERD_PRELOAD_LINKER", "gbif_backbone")
        try:
            threshold = float(os.getenv("DUUI_TAXONERD_PRELOAD_THRESHOLD", "0.7"))
        except ValueError:
            threshold = 0.7
        await asyncio.to_thread(load_taxonerd, model, linker, threshold, exclude, resolve_prefer_gpu(None))

    async def process(self, doc: TaxoNERDLegacyRequest) -> TaxoNERDLegacyResponse:
        result = await asyncio.to_thread(
            run_legacy_procedure,
            doc.text,
            doc.model,
            doc.linking,
            doc.threshold,
            tuple(doc.exclude),
            resolve_prefer_gpu(doc.prefer_gpu),
        )
        rows: list[TaxonLegacyOut] = []
        for taxon in result.taxons:
            features: dict[str, Any] = dict(taxon.features or {})
            rows.append(TaxonLegacyOut(
                begin=taxon.begin,
                end=taxon.end,
                comment=[GBIFComment(
                    id=str(features.get(LINK_ID_FEATURE, taxon.identifier or "") or ""),
                    value=str(features.get(LINK_VALUE_FEATURE, taxon.value or "") or ""),
                    propability=float(features.get(LINK_SCORE_FEATURE, 0.0) or 0.0),
                )],
            ))
        return TaxoNERDLegacyResponse(taxons=rows)


app = create_app(TaxoNERDLegacyAnnotator)
