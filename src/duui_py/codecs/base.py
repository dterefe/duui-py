from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Any, Protocol, TypeVar, runtime_checkable

RequestT = TypeVar("RequestT", covariant=True)
ResponseT = TypeVar("ResponseT", contravariant=True)

class Codec(Protocol[RequestT, ResponseT]):
    name: str
    request_media_type: str
    response_media_type: str

    def communication_layer_content(self) -> dict[str, Any]: ...
    def decode_request(self, body: bytes) -> RequestT: ...
    def encode_response(self, result: ResponseT) -> bytes: ...


@runtime_checkable
class StreamingRequestDecoder(Protocol[RequestT]):
    async def decode_request_stream(self, body_stream: AsyncIterable[bytes]) -> RequestT | AsyncIterable[RequestT]: ...


@runtime_checkable
class StreamingResponseEncoder(Protocol[ResponseT]):
    async def encode_response_stream(self, result_stream: AsyncIterable[ResponseT]) -> AsyncIterable[bytes]: ...
