from __future__ import annotations

from typing import Any, Optional, TypeAlias, cast

import msgpack
from pydantic import BaseModel, Field

from duui_py.codecs.base import Codec
from duui_py.models import (
    AnnotationMeta,
    DocumentModification,
    DuuiDocument,
    DuuiResult,
    FsRec,
    SofaPayload,
)
from duui_py.models.fs_builder import build_feature_structures

MsgpackScalar: TypeAlias = None | bool | int | float | str | bytes
MsgpackValue: TypeAlias = MsgpackScalar | list["MsgpackValue"] | dict[str, "MsgpackValue"]
MsgpackObject: TypeAlias = dict[str, MsgpackValue]


class WireEnvelopeIn(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
    view: str = ""
    sofa: SofaPayload
    fs: list[FsRec] = Field(default_factory=list)


class WireEnvelopeOut(BaseModel):
    sofa: Optional[SofaPayload] = None
    fs: list[FsRec] = Field(default_factory=list)
    meta: Optional[AnnotationMeta] = None
    modification_meta: Optional[DocumentModification] = None
    errors: list[str] = Field(default_factory=list)


def decode_msgpack(raw: bytes) -> MsgpackObject:
    unpacked = cast(object, msgpack.unpackb(raw, raw=False, strict_map_key=False))
    if not isinstance(unpacked, dict) or not all(isinstance(k, str) for k in unpacked):
        raise TypeError("Expected msgpack object with string keys")
    return cast(MsgpackObject, unpacked)


def encode_msgpack(obj: MsgpackObject) -> bytes:
    return cast(bytes, msgpack.packb(obj, use_bin_type=True))


def wire_to_document(env: WireEnvelopeIn) -> DuuiDocument:
    return DuuiDocument(
        parameters=env.parameters,
        view=env.view,
        sofa=env.sofa,
        fs=env.fs,
    )


def result_to_wire(result: DuuiResult) -> WireEnvelopeOut:
    if result.feature_structures:
        return WireEnvelopeOut(
            sofa=result.sofa,
            fs=build_feature_structures(result.feature_structures),
            meta=result.meta,
            modification_meta=result.modification_meta,
            errors=result.errors,
        )

    fs: list[FsRec] = []
    next_id = 1
    for a in result.annotations:
        fs.append(FsRec(id=next_id, ref=a.ref, type=a.type, begin=a.begin, end=a.end, features=a.features))
        next_id += 1

    return WireEnvelopeOut(
        sofa=result.sofa,
        fs=fs,
        meta=result.meta,
        modification_meta=result.modification_meta,
        errors=result.errors,
    )


class DuuiBinV1MsgpackCodec(Codec[DuuiDocument, DuuiResult]):
    name = "duui-bin-v1-msgpack"
    request_media_type = "application/x-msgpack"
    response_media_type = "application/x-msgpack"
    communication_layer_kind = "duui-bin-v1"
    communication_layer_format = "messagepack"
    communication_layer_version = 1

    def communication_layer_content(self) -> dict[str, str | int]:
        return {
            "kind": self.communication_layer_kind,
            "format": self.communication_layer_format,
            "version": self.communication_layer_version,
            "spec": self.name,
        }

    def decode_request(self, body: bytes) -> DuuiDocument:
        env_in = WireEnvelopeIn.model_validate(decode_msgpack(body))
        return wire_to_document(env_in)

    def encode_response(self, result: DuuiResult) -> bytes:
        env_out = result_to_wire(result).model_dump(by_alias=True)
        return encode_msgpack(env_out)
