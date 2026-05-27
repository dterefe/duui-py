from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from duui_py.logging.core import AnyEvent
from duui_py.telemetry import (
    DEFAULT_SCOPES,
    SUPPORTED_SCOPES,
    TELEMETRY_PROTOCOL_VERSION,
    host_resource_attributes,
)


class StreamRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    annotator_id: str | None = None
    replica_id: str | None = None
    application_id: str | None = None
    orchestrator_id: str | None = None
    machine_id: str | None = None
    component_id: str | None = None
    pipeline_run_id: str | None = None
    ttl_minutes: int = Field(default=5, ge=1, le=60)


class StreamRegistrationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stream_id: str
    expires_at: datetime


class StreamInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stream_id: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    identifiers: dict[str, str | None]


class StreamConnection:
    def __init__(
        self,
        stream_id: str,
        identifiers: dict[str, str | None],
        expires_at: datetime,
        max_queue_size: int,
    ):
        self.stream_id = stream_id
        self.identifiers = identifiers
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = self.created_at
        self.expires_at = expires_at
        self._queue: asyncio.Queue[AnyEvent | None] = asyncio.Queue(maxsize=max_queue_size)
        self._active = True

    async def send(self, event: AnyEvent) -> None:
        if not self._active:
            return
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
                self._queue.put_nowait(event)
            except asyncio.QueueEmpty:
                return

    async def events(self) -> AsyncIterator[bytes]:
        handshake = {
            "stream_id": self.stream_id,
            "identifiers": self.identifiers,
            "resource": host_resource_attributes(),
            "supported_scopes": sorted(SUPPORTED_SCOPES),
            "default_scopes": list(DEFAULT_SCOPES),
            "telemetry_protocol_version": TELEMETRY_PROTOCOL_VERSION,
        }
        import json

        yield f"event: handshake\ndata: {json.dumps(handshake, separators=(',', ':'))}\n\n".encode("utf-8")
        while self._active:
            if datetime.now(timezone.utc) > self.expires_at:
                break
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=30)
            except asyncio.TimeoutError:
                self.last_activity = datetime.now(timezone.utc)
                yield b"event: keepalive\ndata: {}\n\n"
                continue

            if event is None:
                break
            self.last_activity = datetime.now(timezone.utc)
            yield f"event: {event.type.value}\ndata: {event.model_dump_json()}\n\n".encode("utf-8")
            self._queue.task_done()

    def close(self) -> None:
        self._active = False
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            pass

    def info(self) -> StreamInfo:
        return StreamInfo(
            stream_id=self.stream_id,
            created_at=self.created_at,
            expires_at=self.expires_at,
            last_activity=self.last_activity,
            identifiers=self.identifiers,
        )


class StreamManager:
    def __init__(self, default_ttl_minutes: int = 5, max_queue_size: int = 1000):
        self.default_ttl_minutes = default_ttl_minutes
        self.max_queue_size = max_queue_size
        self._streams: dict[str, StreamConnection] = {}
        self._lock = asyncio.Lock()

    def start(self) -> None:
        return None

    def has_streams(self) -> bool:
        return bool(self._streams)

    async def stop(self) -> None:
        async with self._lock:
            streams = list(self._streams.values())
            self._streams.clear()
        for stream in streams:
            stream.close()

    async def open_stream(
        self,
        identifiers: dict[str, str | None] | None = None,
        ttl_minutes: int | None = None,
    ) -> StreamConnection:
        now = datetime.now(timezone.utc)
        stream_id = str(uuid4())
        ttl = ttl_minutes or self.default_ttl_minutes
        stream = StreamConnection(
            stream_id=stream_id,
            identifiers=identifiers or {},
            expires_at=now + timedelta(minutes=ttl),
            max_queue_size=self.max_queue_size,
        )
        async with self._lock:
            self._streams[stream_id] = stream
        return stream

    async def register_stream(
        self,
        identifiers: dict[str, str | None],
        ttl_minutes: int | None = None,
        client_info: dict[str, str] | None = None,
    ) -> StreamRegistrationResponse:
        del client_info
        stream = await self.open_stream(identifiers=identifiers, ttl_minutes=ttl_minutes)
        return StreamRegistrationResponse(stream_id=stream.stream_id, expires_at=stream.expires_at)

    async def remove_stream(self, stream_id: str) -> bool:
        async with self._lock:
            stream = self._streams.pop(stream_id, None)
        if stream is None:
            return False
        stream.close()
        return True

    async def broadcast_event(self, event: AnyEvent) -> None:
        async with self._lock:
            streams = list(self._streams.values())
        for stream in streams:
            await stream.send(event)

    async def get_stream_info(self, stream_id: str) -> StreamInfo | None:
        async with self._lock:
            stream = self._streams.get(stream_id)
        return stream.info() if stream is not None else None

    async def list_streams(self) -> list[StreamInfo]:
        async with self._lock:
            streams = list(self._streams.values())
        return [stream.info() for stream in streams]


_stream_manager_instance: StreamManager | None = None


def get_stream_manager() -> StreamManager:
    global _stream_manager_instance
    if _stream_manager_instance is None:
        _stream_manager_instance = StreamManager()
    return _stream_manager_instance


def configure_stream_manager(default_ttl_minutes: int = 5, max_queue_size: int = 1000) -> StreamManager:
    global _stream_manager_instance
    _stream_manager_instance = StreamManager(
        default_ttl_minutes=default_ttl_minutes,
        max_queue_size=max_queue_size,
    )
    return _stream_manager_instance
