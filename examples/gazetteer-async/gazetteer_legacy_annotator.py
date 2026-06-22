from __future__ import annotations

from typing import Any

from pydantic import BaseModel

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

from gazetteer_annotator import _configure_gazetteer_backend, _gazetteer_backend


LEGACY_LUA = r'''
StandardCharsets = luajava.bindClass("java.nio.charset.StandardCharsets")
function serialize(inputCas, outputStream, parameters)
    parameters = parameters or {}
    local payload = { text = inputCas:getDocumentText() }
    if parameters.max_len ~= nil then payload.max_len = parameters.max_len end
    if parameters.result_selection ~= nil then payload.result_selection = parameters.result_selection end
    if parameters.timeout_seconds ~= nil then payload.timeout_seconds = tonumber(parameters.timeout_seconds) end
    if parameters.timeout ~= nil then payload.timeout_seconds = tonumber(parameters.timeout) end
    outputStream:write(json.encode(payload))
end
function deserialize(inputCas, inputStream)
    local inputString = luajava.newInstance("java.lang.String", inputStream:readAllBytes(), StandardCharsets.UTF_8)
    local results = json.decode(inputString)
    for _, match in ipairs(results or {}) do
        local taxon = luajava.newInstance("org.texttechnologylab.annotation.type.Taxon", inputCas)
        taxon:setBegin(match.begin)
        taxon:setEnd(match["end"])
        if match.match_strings ~= nil then taxon:setValue(match.match_strings) end
        if match.match_labels ~= nil then taxon:setIdentifier(match.match_labels) end
        taxon:addToIndexes()
    end
end
'''


class GazetteerLegacyRequest(BaseModel):
    text: str
    max_len: int | None = None
    result_selection: str | None = None
    timeout_seconds: float = 120.0


class GazetteerLegacyAnnotator(
    DuuiAnnotator[GazetteerLegacyRequest, list[dict[str, Any]]]
):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "bagci BioFID gazetteer legacy Lua JSON"}),
        descriptor=AnnotatorDescriptor(
            name="gazetteer-legacy-lua-json",
            version="1.0.0",
            input=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json"))),
            output=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json"))),
        ),
        typesystem_xml_path="TypeSystemGazetteer.xml",
        parameters_schema={
            "max_len": {"type": "integer", "description": "Maximum length forwarded to gazetteer-rs."},
            "result_selection": {"type": "string", "description": "Result-selection mode forwarded to gazetteer-rs."},
            "timeout_seconds": {"type": "number", "default": 120.0, "description": "Backend request timeout."},
            "timeout": {"type": "number", "default": 120.0, "description": "Alias for timeout_seconds."},
        },
    )

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._pool: ManagedHttpPool | None = None

    def codec(self) -> LuaCustomCodec[GazetteerLegacyRequest, list[dict[str, Any]]]:
        return LuaCustomCodec(
            LEGACY_LUA,
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=GazetteerLegacyRequest.model_validate_json,
            encode_response=lambda result: __import__("json").dumps(result, separators=(",", ":")).encode("utf-8"),
            name="gazetteer-legacy-lua-json",
        )

    async def startup(self) -> None:
        _configure_gazetteer_backend()
        backend_url = await _gazetteer_backend.ensure_running({})
        self._pool = ManagedHttpPool(backend_url)

    async def shutdown(self) -> None:
        if self._pool is not None:
            await self._pool.close()
        await _gazetteer_backend.shutdown()
        await shutdown_all_clients()

    async def process(self, doc: GazetteerLegacyRequest) -> list[dict[str, Any]]:
        if self._pool is None:
            await self.startup()
        assert self._pool is not None
        if self._pool._timeout != doc.timeout_seconds:
            await self._pool.close()
            backend_url = await _gazetteer_backend.ensure_running({})
            self._pool = ManagedHttpPool(backend_url, timeout=doc.timeout_seconds)
        payload: dict[str, Any] = {"text": doc.text}
        if doc.max_len is not None:
            payload["max_len"] = doc.max_len
        if doc.result_selection is not None:
            payload["result_selection"] = doc.result_selection
        response = await self._pool.query("/v1/process", payload)
        return response if isinstance(response, list) else []


app = create_app(GazetteerLegacyAnnotator)
