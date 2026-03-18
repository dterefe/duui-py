from __future__ import annotations

from typing import Callable, Generic, TypeVar

from duui_py.codecs.base import Codec

RequestModel = TypeVar("RequestModel")
ResponseModel = TypeVar("ResponseModel")


class LuaCustomCodec(Codec[RequestModel, ResponseModel], Generic[RequestModel, ResponseModel]):
    def __init__(
        self,
        communication_lua: str,
        *,
        request_media_type: str,
        response_media_type: str,
        decode_request: Callable[[bytes], RequestModel],
        encode_response: Callable[[ResponseModel], bytes],
        name: str = "lua-custom",
    ):
        self._lua = communication_lua
        self._decode_request = decode_request
        self._encode_response = encode_response
        self.name = name
        self.request_media_type = request_media_type
        self.response_media_type = response_media_type

    def communication_layer_content(self) -> dict[str, str | int]:
        return {
            "kind": "custom",
            "format": "lua",
            "version": 1,
            "spec": self._lua,
        }

    def decode_request(self, body: bytes) -> RequestModel:
        return self._decode_request(body)

    def encode_response(self, result: ResponseModel) -> bytes:
        return self._encode_response(result)
