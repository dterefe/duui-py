from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from contextvars import ContextVar
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from duui_py.models.config import AnnotatorDescriptor
    from duui_py.logging.streaming import StreamManager
    from duui_py.logging.context import EventContext
else:
    AnnotatorDescriptor = object


class EventType(str, Enum):
    LOG = "log"
    METRIC = "metric"
    ERROR = "error"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Event(BaseModel):
    """Base event model for all logging events."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    context: Dict[str, str] = Field(default_factory=dict)
    annotator_config: Optional[Dict[str, str]] = None


class LogEvent(Event):
    """Event for standard log messages."""
    type: EventType = EventType.LOG
    level: LogLevel
    message: str
    extra: Dict[str, Any] = Field(default_factory=dict)


class MetricEvent(Event):
    """Event for resource metrics."""
    type: EventType = EventType.METRIC
    category: str  # e.g., "cpu", "memory", "disk", "network"
    name: str      # e.g., "cpu_percent", "memory_rss_bytes"
    value: float
    unit: str      # e.g., "percent", "bytes", "bytes_per_second"
    interval_ms: int = 0  # Time span over which metric was measured
    tags: Dict[str, str] = Field(default_factory=dict)


class ErrorEvent(Event):
    """Event for structured error reporting."""
    type: EventType = EventType.ERROR
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


# Type alias for any event
AnyEvent = Union[LogEvent, MetricEvent, ErrorEvent]


class EventSink:
    """Abstract base class for event sinks."""
    
    async def send(self, event: AnyEvent) -> None:
        """Send an event to the sink."""
        raise NotImplementedError
    
    async def close(self) -> None:
        """Close the sink and release resources."""
        pass


class StreamSink(EventSink):
    """Sink that sends events to active streams."""
    
    def __init__(self, stream_manager: StreamManager):
        self.stream_manager = stream_manager
    
    async def send(self, event: AnyEvent) -> None:
        """Send event to all active streams."""
        await self.stream_manager.broadcast_event(event)


class ConsoleSink(EventSink):
    """Sink that prints events to console (for debugging)."""
    
    async def send(self, event: AnyEvent) -> None:
        """Print event to console."""
        print(f"[{event.timestamp.isoformat()}] {event.type.value}: {event.model_dump_json()}")


class EventLogger:
    """Central logging class for handling events."""
    
    def __init__(
        self,
        sinks: Optional[List[EventSink]] = None,
        default_context: Optional[Dict[str, str]] = None,
        annotator_descriptor: Optional[AnnotatorDescriptor] = None,
    ):
        self.sinks = sinks or []
        self.default_context = default_context or {}
        self.annotator_descriptor = annotator_descriptor
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None
        
    def start(self) -> None:
        """Start the background worker for async event processing."""
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=1000)
            self._worker_task = asyncio.create_task(self._worker_loop())
    
    async def stop(self) -> None:
        """Stop the background worker and wait for completion."""
        if self._queue is not None:
            await self._queue.put(None)  # Sentinel to stop worker
            if self._worker_task:
                await self._worker_task
            self._queue = None
            self._worker_task = None
    
    async def _worker_loop(self) -> None:
        """Background worker that processes events from the queue."""
        if self._queue is None:
            return
        
        while True:
            event = await self._queue.get()
            if event is None:  # Sentinel to stop
                break
            
            try:
                await self._send_event(event)
            except Exception as e:
                # Log but don't crash worker
                print(f"Error sending event: {e}")
            finally:
                self._queue.task_done()
    
    async def _send_event(self, event: AnyEvent) -> None:
        """Send event to all sinks."""
        for sink in self.sinks:
            try:
                await sink.send(event)
            except Exception as e:
                print(f"Error in sink {sink.__class__.__name__}: {e}")
    
    async def _enqueue_event(self, event: AnyEvent) -> None:
        """Enqueue an event for async processing."""
        if self._queue is None:
            # If not started, send synchronously
            await self._send_event(event)
        else:
            try:
                self._queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest event to make room
                try:
                    self._queue.get_nowait()
                    self._queue.put_nowait(event)
                except asyncio.QueueEmpty:
                    pass  # Should not happen
    
    def _build_event_context(self) -> Dict[str, str]:
        """Build context from default context and current event context."""
        from duui_py.logging.context import get_event_context
        
        context = self.default_context.copy()
        
        # Add current request context if available
        event_context = get_event_context()
        if event_context:
            context.update(event_context.context)
        
        return context
    
    def _build_annotator_config(self) -> Optional[Dict[str, str]]:
        """Build annotator config info from descriptor."""
        if not self.annotator_descriptor:
            return None
        
        return {
            "name": self.annotator_descriptor.name,
            "version": self.annotator_descriptor.version,
        }
    
    async def log(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a message with the specified level."""
        event = LogEvent(
            level=level,
            message=message,
            extra=extra or {},
            context=self._build_event_context(),
            annotator_config=self._build_annotator_config(),
        )
        await self._enqueue_event(event)
    
    async def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message."""
        await self.log(LogLevel.DEBUG, message, extra)
    
    async def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message."""
        await self.log(LogLevel.INFO, message, extra)
    
    async def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message."""
        await self.log(LogLevel.WARNING, message, extra)
    
    async def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an error message."""
        await self.log(LogLevel.ERROR, message, extra)
    
    async def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a critical message."""
        await self.log(LogLevel.CRITICAL, message, extra)
    
    async def metric(
        self,
        category: str,
        name: str,
        value: float,
        unit: str,
        interval_ms: int = 0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Log a metric."""
        event = MetricEvent(
            category=category,
            name=name,
            value=value,
            unit=unit,
            interval_ms=interval_ms,
            tags=tags or {},
            context=self._build_event_context(),
            annotator_config=self._build_annotator_config(),
        )
        await self._enqueue_event(event)
    
    async def error_event(
        self,
        error_type: str,
        message: str,
        stack_trace: Optional[str] = None,
        recovery_suggestion: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a structured error event."""
        event = ErrorEvent(
            error_type=error_type,
            message=message,
            stack_trace=stack_trace,
            recovery_suggestion=recovery_suggestion,
            extra=extra or {},
            context=self._build_event_context(),
            annotator_config=self._build_annotator_config(),
        )
        await self._enqueue_event(event)


# Global logger instance
_logger_instance: Optional[EventLogger] = None
_logger_context: ContextVar[Optional[EventLogger]] = ContextVar("event_logger", default=None)


def get_event_logger() -> EventLogger:
    """Get the global event logger instance."""
    global _logger_instance
    if _logger_instance is None:
        raise RuntimeError("Event logger not configured. Call configure_logger() first.")
    return _logger_instance


def configure_logger(
    sinks: Optional[List[EventSink]] = None,
    default_context: Optional[Dict[str, str]] = None,
    annotator_descriptor: Optional[AnnotatorDescriptor] = None,
    start_background_worker: bool = True,
) -> EventLogger:
    """Configure the global event logger."""
    global _logger_instance
    
    if _logger_instance is not None:
        raise RuntimeError("Event logger already configured")
    
    _logger_instance = EventLogger(
        sinks=sinks,
        default_context=default_context,
        annotator_descriptor=annotator_descriptor,
    )
    
    if start_background_worker:
        _logger_instance.start()
    
    return _logger_instance