from __future__ import annotations

from typing import Any, Protocol, TypeVar

RequestT = TypeVar("RequestT", covariant=True)
ResponseT = TypeVar("ResponseT", contravariant=True)

class Codec(Protocol[RequestT, ResponseT]):
    name: str
    request_media_type: str
    response_media_type: str

    def communication_layer_content(self) -> dict[str, Any]: ...
    def decode_request(self, body: bytes) -> RequestT: ...
    def encode_response(self, result: ResponseT) -> bytes: ...
