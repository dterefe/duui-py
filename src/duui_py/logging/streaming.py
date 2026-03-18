from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from duui_py.logging.core import AnyEvent, Event, get_event_logger


class StreamRegistrationRequest(BaseModel):
    """Request body for stream registration."""
    model_config = ConfigDict(extra="forbid")
    
    annotator_id: Optional[str] = None
    replica_id: Optional[str] = None
    application_id: Optional[str] = None
    artifact_id: Optional[str] = None
    request_id: Optional[str] = None
    ttl_minutes: int = Field(default=5, ge=1, le=60)


class StreamRegistrationResponse(BaseModel):
    """Response for stream registration."""
    model_config = ConfigDict(extra="forbid")
    
    stream_id: str
    expires_at: datetime


class StreamInfo(BaseModel):
    """Information about an active stream."""
    model_config = ConfigDict(extra="forbid")
    
    stream_id: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    identifiers: Dict[str, Optional[str]]
    client_info: Optional[Dict[str, str]] = None


class StreamConnection:
    """Represents a single SSE stream connection."""
    
    def __init__(self, stream_id: str, identifiers: Dict[str, Optional[str]]):
        self.stream_id = stream_id
        self.identifiers = identifiers
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = self.created_at
        self.expires_at = self.created_at  # Will be set by StreamManager
        self._queue: asyncio.Queue[Optional[AnyEvent]] = asyncio.Queue(maxsize=1000)
        self._active = True
        self.client_info: Optional[Dict[str, str]] = None
    
    async def send(self, event: AnyEvent) -> None:
        """Send an event to this stream."""
        if not self._active:
            return
        
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            # Drop oldest event to make room
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(event)
            except asyncio.QueueEmpty:
                pass  # Should not happen
    
    async def events(self) -> AsyncIterator[bytes]:
        """Generator that yields SSE formatted events."""
        while self._active:
            try:
                # Wait for event with timeout for heartbeat
                event = await asyncio.wait_for(self._queue.get(), timeout=30)
                
                if event is None:  # Sentinel to stop
                    break
                
                # Update last activity
                self.last_activity = datetime.now(timezone.utc)
                
                # Format as SSE
                data = json.dumps(event.model_dump())
                yield f"data: {data}\n\n".encode('utf-8')
                
                self._queue.task_done()
                
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield ":keepalive\n\n".encode('utf-8')
                # Update last activity for heartbeat
                self.last_activity = datetime.now(timezone.utc)
            except Exception:
                # Connection likely closed
                break
    
    def close(self) -> None:
        """Close the stream connection."""
        self._active = False
        # Put sentinel to wake up waiting generator
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
    
    def is_expired(self) -> bool:
        """Check if the stream has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)


class StreamManager:
    """Manages active SSE streams and stream lifecycle."""
    
    def __init__(self, default_ttl_minutes: int = 5):
        self.default_ttl_minutes = default_ttl_minutes
        self._streams: Dict[str, StreamConnection] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def start(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self) -> None:
        """Stop the background cleanup task and close all streams."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        # Close all streams
        async with self._lock:
            for stream in self._streams.values():
                stream.close()
            self._streams.clear()
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired streams."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_expired_streams()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log but don't crash
                print(f"Error in stream cleanup: {e}")
    
    async def _cleanup_expired_streams(self) -> None:
        """Remove expired streams."""
        async with self._lock:
            expired_ids = [
                stream_id for stream_id, stream in self._streams.items()
                if stream.is_expired()
            ]
            
            for stream_id in expired_ids:
                stream = self._streams.pop(stream_id)
                stream.close()
    
    async def register_stream(
        self,
        identifiers: Dict[str, Optional[str]],
        ttl_minutes: Optional[int] = None,
        client_info: Optional[Dict[str, str]] = None,
    ) -> StreamRegistrationResponse:
        """Register a new stream and return its ID."""
        stream_id = str(uuid4())
        ttl = ttl_minutes or self.default_ttl_minutes
        
        stream = StreamConnection(stream_id=stream_id, identifiers=identifiers)
        stream.expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl)
        stream.client_info = client_info
        
        async with self._lock:
            self._streams[stream_id] = stream
        
        return StreamRegistrationResponse(
            stream_id=stream_id,
            expires_at=stream.expires_at,
        )
    
    async def get_stream(self, stream_id: str) -> Optional[StreamConnection]:
        """Get a stream by ID, updating its activity."""
        async with self._lock:
            stream = self._streams.get(stream_id)
            if stream:
                stream.update_activity()
            return stream
    
    async def remove_stream(self, stream_id: str) -> bool:
        """Remove a stream by ID."""
        async with self._lock:
            stream = self._streams.pop(stream_id, None)
            if stream:
                stream.close()
                return True
            return False
    
    async def broadcast_event(self, event: AnyEvent) -> None:
        """Broadcast an event to all active streams."""
        async with self._lock:
            streams = list(self._streams.values())
        
        # Send to all streams in parallel
        tasks = [stream.send(event) for stream in streams]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_stream_info(self, stream_id: str) -> Optional[StreamInfo]:
        """Get information about a stream."""
        stream = await self.get_stream(stream_id)
        if not stream:
            return None
        
        return StreamInfo(
            stream_id=stream.stream_id,
            created_at=stream.created_at,
            expires_at=stream.expires_at,
            last_activity=stream.last_activity,
            identifiers=stream.identifiers,
            client_info=stream.client_info,
        )
    
    async def list_streams(self) -> List[StreamInfo]:
        """Get information about all active streams."""
        async with self._lock:
            streams = list(self._streams.values())
        
        return [
            StreamInfo(
                stream_id=stream.stream_id,
                created_at=stream.created_at,
                expires_at=stream.expires_at,
                last_activity=stream.last_activity,
                identifiers=stream.identifiers,
                client_info=stream.client_info,
            )
            for stream in streams
        ]


# Global stream manager instance
_stream_manager_instance: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    """Get the global stream manager instance."""
    global _stream_manager_instance
    if _stream_manager_instance is None:
        _stream_manager_instance = StreamManager()
        _stream_manager_instance.start()
    return _stream_manager_instance


def configure_stream_manager(default_ttl_minutes: int = 5) -> StreamManager:
    """Configure the global stream manager."""
    global _stream_manager_instance
    
    if _stream_manager_instance is not None:
        raise RuntimeError("Stream manager already configured")
    
    _stream_manager_instance = StreamManager(default_ttl_minutes=default_ttl_minutes)
    _stream_manager_instance.start()
    
    return _stream_manager_instance


# FastAPI router for streaming endpoints
router = APIRouter(prefix="/v2/events", tags=["events"])


@router.post("/connect", response_model=StreamRegistrationResponse)
async def connect_stream(
    request: Request,
    registration: StreamRegistrationRequest,
) -> StreamRegistrationResponse:
    """
    Register a new event stream.
    
    Returns a stream_id that can be used to connect to the SSE stream.
    """
    stream_manager = get_stream_manager()
    
    # Extract client info
    client_info = {
        "user_agent": request.headers.get("user-agent", ""),
        "remote_addr": request.client.host if request.client else "unknown",
    }
    
    # Build identifiers
    identifiers = {
        "annotator_id": registration.annotator_id,
        "replica_id": registration.replica_id,
        "application_id": registration.application_id,
        "artifact_id": registration.artifact_id,
        "request_id": registration.request_id,
    }
    
    return await stream_manager.register_stream(
        identifiers=identifiers,
        ttl_minutes=registration.ttl_minutes,
        client_info=client_info,
    )


@router.get("/stream")
async def stream_events(
    stream_id: str,
    request: Request,
) -> StreamingResponse:
    """
    Server-Sent Events (SSE) stream for receiving events.
    
    Connect with the stream_id obtained from /connect.
    """
    stream_manager = get_stream_manager()
    
    stream = await stream_manager.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found or expired")
    
    async def event_generator() -> AsyncIterator[bytes]:
        """Generator that yields SSE events."""
        try:
            async for event_data in stream.events():
                yield event_data
        finally:
            # Ensure stream is cleaned up
            await stream_manager.remove_stream(stream_id)
    
    return StreamingResponse(
        content=event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        },
    )


@router.get("/info/{stream_id}", response_model=StreamInfo)
async def get_stream_info(stream_id: str) -> StreamInfo:
    """Get information about a specific stream."""
    stream_manager = get_stream_manager()
    
    info = await stream_manager.get_stream_info(stream_id)
    if not info:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    return info


@router.get("/list", response_model=List[StreamInfo])
async def list_streams() -> List[StreamInfo]:
    """List all active streams."""
    stream_manager = get_stream_manager()
    return await stream_manager.list_streams()


@router.delete("/{stream_id}")
async def disconnect_stream(stream_id: str) -> Dict[str, bool]:
    """Manually disconnect a stream."""
    stream_manager = get_stream_manager()
    
    success = await stream_manager.remove_stream(stream_id)
    return {"success": success}