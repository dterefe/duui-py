from __future__ import annotations

import time
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, Iterator


_CURRENT_WIRE_PROFILE: ContextVar["WireProfile | None"] = ContextVar(
    "duui_current_wire_profile", default=None
)


@dataclass
class WireProfile:
    protocol: str = "unknown"
    compression: str = "none"
    chunks: int = 0
    start_chunks: int = 0
    sofa_chunks: int = 0
    batch_chunks: int = 0
    error_chunks: int = 0
    end_chunks: int = 0
    row_batches: int = 0
    column_batches: int = 0
    compressed_batches: int = 0
    direct_batches: int = 0
    rows: int = 0
    feature_columns: int = 0
    payload_bytes: int = 0
    frame_bytes: int = 0
    build_batch_ms: float = 0.0
    pack_msgpack_ms: float = 0.0
    compress_ms: float = 0.0
    decode_chunk_ms: float = 0.0
    decoded_chunks: int = 0
    decoded_payload_bytes: int = 0
    first_frame_ms: float | None = None
    _started: float = field(default_factory=time.perf_counter)

    def set_plan(self, *, protocol: str, compression: str) -> None:
        self.protocol = protocol
        self.compression = compression

    def add_chunk(self, chunk_type: int, payload_len: int) -> None:
        self.chunks += 1
        self.payload_bytes += payload_len
        self.frame_bytes += payload_len + (17 if self.protocol.startswith("runtime-") else 5)
        if self.first_frame_ms is None:
            self.first_frame_ms = (time.perf_counter() - self._started) * 1000.0
        if chunk_type == 0x01:
            self.start_chunks += 1
        elif chunk_type == 0x02:
            self.sofa_chunks += 1
        elif chunk_type == 0x05:
            self.end_chunks += 1
        elif chunk_type == 0x06:
            self.error_chunks += 1
        elif chunk_type == 0x10:
            self.batch_chunks += 1
            self.row_batches += 1
        elif chunk_type == 0x11:
            self.batch_chunks += 1
            self.column_batches += 1
        elif chunk_type == 0x12:
            self.batch_chunks += 1
            self.compressed_batches += 1
        elif chunk_type == 0x13:
            self.batch_chunks += 1
            self.direct_batches += 1
        elif chunk_type == 0x14:
            self.batch_chunks += 1
            self.direct_batches += 1

    def add_decoded_chunk(self, payload_len: int, elapsed_ms: float) -> None:
        self.decoded_chunks += 1
        self.decoded_payload_bytes += payload_len
        self.decode_chunk_ms += elapsed_ms

    def span_attributes(self) -> dict[str, str]:
        values: dict[str, Any] = {
            "duui.wire.protocol": self.protocol,
            "duui.wire.compression": self.compression,
            "duui.wire.chunks": self.chunks,
            "duui.wire.start_chunks": self.start_chunks,
            "duui.wire.sofa_chunks": self.sofa_chunks,
            "duui.wire.batch_chunks": self.batch_chunks,
            "duui.wire.error_chunks": self.error_chunks,
            "duui.wire.end_chunks": self.end_chunks,
            "duui.wire.row_batches": self.row_batches,
            "duui.wire.column_batches": self.column_batches,
            "duui.wire.compressed_batches": self.compressed_batches,
            "duui.wire.direct_batches": self.direct_batches,
            "duui.wire.rows": self.rows,
            "duui.wire.feature_columns": self.feature_columns,
            "duui.wire.payload_bytes": self.payload_bytes,
            "duui.wire.frame_bytes": self.frame_bytes,
            "duui.wire.build_batch_ms": self.build_batch_ms,
            "duui.wire.pack_msgpack_ms": self.pack_msgpack_ms,
            "duui.wire.compress_ms": self.compress_ms,
            "duui.wire.decode_chunk_ms": self.decode_chunk_ms,
            "duui.wire.decoded_chunks": self.decoded_chunks,
            "duui.wire.decoded_payload_bytes": self.decoded_payload_bytes,
        }
        if self.first_frame_ms is not None:
            values["duui.wire.first_frame_ms"] = self.first_frame_ms
        return {
            key: str(int(value)) if isinstance(value, float) else str(value)
            for key, value in values.items()
        }

    def metric_points(self) -> list[tuple[str, str, float, str, int, dict[str, str]]]:
        tags = {"protocol": self.protocol, "compression": self.compression}
        return [
            ("wire", "duui.wire.chunks", float(self.chunks), "count", 0, tags),
            ("wire", "duui.wire.rows", float(self.rows), "count", 0, tags),
            ("wire", "duui.wire.payload_bytes", float(self.payload_bytes), "bytes", 0, tags),
            ("wire", "duui.wire.frame_bytes", float(self.frame_bytes), "bytes", 0, tags),
            (
                "wire",
                "duui.wire.build_batch_ms",
                self.build_batch_ms,
                "milliseconds",
                int(self.build_batch_ms),
                tags,
            ),
            (
                "wire",
                "duui.wire.pack_msgpack_ms",
                self.pack_msgpack_ms,
                "milliseconds",
                int(self.pack_msgpack_ms),
                tags,
            ),
            ("wire", "duui.wire.compress_ms", self.compress_ms, "milliseconds", int(self.compress_ms), tags),
            ("wire", "duui.wire.decode_chunk_ms", self.decode_chunk_ms, "milliseconds", int(self.decode_chunk_ms), tags),
        ]


def begin_wire_profile() -> Token[WireProfile | None]:
    return _CURRENT_WIRE_PROFILE.set(WireProfile())


def end_wire_profile(token: Token[WireProfile | None]) -> WireProfile | None:
    profile = _CURRENT_WIRE_PROFILE.get()
    _CURRENT_WIRE_PROFILE.reset(token)
    return profile


def current_wire_profile() -> WireProfile | None:
    return _CURRENT_WIRE_PROFILE.get()


@contextmanager
def timed_profile_field(field_name: str) -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        profile = current_wire_profile()
        if profile is not None:
            current = getattr(profile, field_name)
            setattr(
                profile,
                field_name,
                current + (time.perf_counter() - started) * 1000.0,
            )
