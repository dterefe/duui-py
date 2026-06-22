from __future__ import annotations

from typing import Any, Literal

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
from duui_py.utils.backend import ManagedHttpPool, shutdown_all_clients

from gnfinder_annotator import _api_language, _configure_gnfinder_backend, _gnfinder_backend


LEGACY_LUA = r'''
StandardCharsets = luajava.bindClass("java.nio.charset.StandardCharsets")
function serialize(inputCas, outputStream, parameters)
    parameters = parameters or {}
    outputStream:write(json.encode({
        text = inputCas:getDocumentText(),
        language = parameters.language or parameters.lang or "detect",
        ambiguousNames = parameters.ambiguousNames == "true",
        noBayes = parameters.noBayes == "true",
        oddsDetails = parameters.oddsDetails == "true",
        verification = parameters.verification ~= "false",
        sources = json.decode(parameters.sources or "[11]"),
        allMatches = parameters.allMatches == "true",
        timeout_seconds = tonumber(parameters.timeout_seconds or parameters.timeout) or 120,
    }))
end
function deserialize(inputCas, inputStream)
    local inputString = luajava.newInstance("java.lang.String", inputStream:readAllBytes(), StandardCharsets.UTF_8)
    local results = json.decode(inputString)
    local taxon_results = results.results or {}
    local taxon_references = luajava.newInstance("org.apache.uima.jcas.cas.FSArray", inputCas, #taxon_results)
    for i, taxon in ipairs(taxon_results) do
        local typeName = "org.texttechnologylab.annotation.biofid.gnfinder.Taxon"
        if taxon.recordId ~= nil then
            typeName = "org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon"
        end
        local anno = luajava.newInstance(typeName, inputCas)
        anno:setBegin(taxon.begin)
        anno:setEnd(taxon["end"])
        if taxon.value ~= nil then anno:setValue(taxon.value) end
        if taxon.identifier ~= nil then anno:setIdentifier(taxon.identifier) end
        if taxon.cardinality ~= nil then anno:setCardinality(taxon.cardinality) end
        if taxon.oddsLog10 ~= nil then anno:setOddsLog10(taxon.oddsLog10) end
        if taxon.oddsDetails ~= nil then
            local odds_details = luajava.newInstance("org.apache.uima.jcas.cas.FSArray", inputCas, #taxon.oddsDetails)
            for i, details in ipairs(taxon.oddsDetails) do
                local details_anno = luajava.newInstance("org.texttechnologylab.annotation.biofid.gnfinder.OddsDetails", inputCas)
                details_anno:setFeature(details.feature)
                details_anno:setOdds(details.value)
                details_anno:addToIndexes()
                odds_details:set(i - 1, details_anno)
            end
            odds_details:addToIndexes()
            anno:setOddsDetails(odds_details)
        end
        if taxon.recordId ~= nil then anno:setRecordId(taxon.recordId) end
        anno:addToIndexes()
        taxon_references:set(i - 1, anno)
    end
    taxon_references:addToIndexes()

    local metadata = results.metadata or {}
    local metadata_anno = luajava.newInstance("org.texttechnologylab.annotation.biofid.gnfinder.MetaData", inputCas)
    if metadata.date ~= nil then metadata_anno:setDate(metadata.date) end
    if metadata.version ~= nil then metadata_anno:setVersion(metadata.version) end
    if metadata.language ~= nil then metadata_anno:setLanguage(metadata.language) end
    metadata_anno:setReferences(taxon_references)
    metadata_anno:addToIndexes()

    local modification_anno = luajava.newInstance("org.texttechnologylab.annotation.DocumentModification", inputCas)
    modification_anno:setUser("GNFinder v2")
    modification_anno:setTimestamp(0)
    modification_anno:setComment("GNFinder, " .. tostring(metadata.version or "") .. ", language = " .. tostring(metadata.language or ""))
    modification_anno:addToIndexes()
end
'''


class GNFinderLegacyRequest(BaseModel):
    text: str = Field(min_length=1)
    language: Literal["eng", "ger", "deu", "detect"] = "detect"
    ambiguousNames: bool = False
    noBayes: bool = False
    oddsDetails: bool = False
    verification: bool = True
    sources: list[int] = Field(default_factory=lambda: [11])
    allMatches: bool = False
    timeout_seconds: float = 120.0


class GNFinderLegacyResponse(BaseModel):
    metadata: dict[str, Any]
    results: list[dict[str, Any]]


def _legacy_result(name: dict[str, Any], *, verify: bool) -> dict[str, Any]:
    out: dict[str, Any] = {
        "begin": int(name.get("start", name.get("begin", 0))),
        "end": int(name.get("end", 0)),
        "value": str(name.get("name") or name.get("verbatim") or ""),
        "identifier": str(name.get("id") or name.get("name") or ""),
        "cardinality": name.get("cardinality"),
        "oddsLog10": name.get("oddsLog10"),
    }
    verification = name.get("verification")
    best = verification.get("bestResult") if isinstance(verification, dict) else None
    if verify and isinstance(best, dict):
        out.update({
            "dataSourceId": best.get("dataSourceId"),
            "recordId": best.get("recordId"),
            "globalId": best.get("globalId"),
            "localId": best.get("localId"),
            "outlink": best.get("outlink"),
            "sortScore": best.get("sortScore"),
            "matchedName": best.get("matchedName"),
            "currentName": best.get("currentName"),
            "matchedCanonicalSimple": best.get("matchedCanonicalSimple"),
            "matchedCanonicalFull": best.get("matchedCanonicalFull"),
            "taxonomicStatus": best.get("taxonomicStatus"),
            "matchType": best.get("matchType"),
            "editDistance": best.get("editDistance"),
        })
        out["identifier"] = str(best.get("outlink") or out["identifier"])
        out["value"] = str(best.get("currentName") or out["value"])
    odds_details = name.get("oddsDetails")
    if isinstance(odds_details, list):
        out["oddsDetails"] = [
            {
                "feature": item.get("feature"),
                "value": item.get("value", item.get("odds")),
            }
            for item in odds_details
            if isinstance(item, dict)
        ]
    return out


class GNFinderLegacyAnnotator(
    DuuiAnnotator[GNFinderLegacyRequest, GNFinderLegacyResponse]
):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "duui-uima/duui-gnfinder-v2 legacy Lua JSON"}),
        descriptor=AnnotatorDescriptor(
            name="gnfinder-legacy-lua-json",
            version="1.0.0",
            input=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json"))),
            output=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json"))),
        ),
        typesystem_xml_path="TypeSystemGNFinder.xml",
        parameters_schema={
            "language": {"type": "string", "default": "detect", "description": "GNFinder language hint."},
            "lang": {"type": "string", "default": "detect", "description": "Alias for language."},
            "ambiguousNames": {"type": "boolean", "default": False},
            "noBayes": {"type": "boolean", "default": False},
            "oddsDetails": {"type": "boolean", "default": False},
            "verification": {"type": "boolean", "default": True},
            "sources": {"type": ["array", "string"], "default": [11], "description": "GNFinder source IDs."},
            "allMatches": {"type": "boolean", "default": False},
            "timeout_seconds": {"type": "number", "default": 120.0},
            "timeout": {"type": "number", "default": 120.0, "description": "Alias for timeout_seconds."},
        },
    )

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._pool: ManagedHttpPool | None = None

    def codec(self) -> LuaCustomCodec[GNFinderLegacyRequest, GNFinderLegacyResponse]:
        return LuaCustomCodec(
            LEGACY_LUA,
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=GNFinderLegacyRequest.model_validate_json,
            encode_response=lambda result: result.model_dump_json(by_alias=True).encode("utf-8"),
            name="gnfinder-legacy-lua-json",
        )

    async def startup(self) -> None:
        _configure_gnfinder_backend({})
        backend_url = await _gnfinder_backend.ensure_running({})
        self._pool = ManagedHttpPool(backend_url)

    async def shutdown(self) -> None:
        if self._pool is not None:
            await self._pool.close()
        await _gnfinder_backend.shutdown()
        await shutdown_all_clients()

    async def process(self, doc: GNFinderLegacyRequest) -> GNFinderLegacyResponse:
        if self._pool is None:
            await self.startup()
        assert self._pool is not None
        if self._pool._timeout != doc.timeout_seconds:
            await self._pool.close()
            backend_url = await _gnfinder_backend.ensure_running({})
            self._pool = ManagedHttpPool(backend_url, timeout=doc.timeout_seconds)
        payload: dict[str, Any] = {
            "text": doc.text,
            "language": _api_language(doc.language),
            "verification": doc.verification,
            "sources": doc.sources,
            "allMatches": doc.allMatches,
            "ambiguousNames": doc.ambiguousNames,
            "noBayes": doc.noBayes,
            "oddsDetails": doc.oddsDetails,
        }
        raw = await self._pool.query("/api/v1/find", payload)
        names = raw.get("names", []) if isinstance(raw, dict) else []
        metadata = raw.get("metadata", {}) if isinstance(raw, dict) else {}
        return GNFinderLegacyResponse(
            metadata={
                "date": metadata.get("date") or "",
                "version": metadata.get("version") or raw.get("version", "") if isinstance(raw, dict) else "",
                "language": metadata.get("language") or _api_language(doc.language),
                "other": metadata.get("other") or [],
            },
            results=[
                _legacy_result(name, verify=doc.verification)
                for name in names
                if isinstance(name, dict)
            ],
        )


app = create_app(GNFinderLegacyAnnotator)
