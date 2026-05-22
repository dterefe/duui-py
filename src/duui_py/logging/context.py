from __future__ import annotations

import contextvars
from typing import Optional

from fastapi import Request

from duui_py.telemetry import (
    TelemetryContext,
    create_telemetry_context_from_request,
    parse_event_context_param,
)


EventContext = TelemetryContext


# Context variable for storing current event context
_current_event_context: contextvars.ContextVar[Optional[EventContext]] = contextvars.ContextVar(
    "current_event_context", default=None
)


def get_event_context() -> Optional[EventContext]:
    """Get the current event context for the request."""
    return _current_event_context.get()


def set_event_context(context: EventContext) -> None:
    """Set the current event context for the request."""
    _current_event_context.set(context)


def clear_event_context() -> None:
    """Clear the current event context."""
    _current_event_context.set(None)


def update_event_context(**kwargs: str) -> None:
    """Update the current event context with additional key-value pairs."""
    current = get_event_context()
    if current is None:
        # Create a new context with the provided values
        new_context = EventContext(context=kwargs)
        set_event_context(new_context)
    else:
        # Update existing context
        new_context = EventContext(
            context={**current.context, **kwargs},
            request_id=current.request_id,
            artifact_id=current.artifact_id,
            annotator_id=current.annotator_id,
            replica_id=current.replica_id,
            application_id=current.application_id,
            orchestrator_id=current.orchestrator_id,
            machine_id=current.machine_id,
            component_id=current.component_id,
            pipeline_run_id=current.pipeline_run_id,
            trace_id=current.trace_id,
            parent_span_id=current.parent_span_id,
            span_id=current.span_id,
            tracestate=current.tracestate,
            telemetry=current.telemetry,
        )
        set_event_context(new_context)


def create_event_context_from_request(
    request: Request | None = None,
    event_context_param: Optional[str] = None,
    request_id: Optional[str] = None,
    **extra_context: str,
) -> EventContext:
    if request is not None:
        return create_telemetry_context_from_request(request, event_context_param=event_context_param)
    context_dict = parse_event_context_param(event_context_param)
    context_dict.update(extra_context)
    return EventContext(
        context=context_dict,
        request_id=request_id or context_dict.pop("request_id", None),
        artifact_id=context_dict.pop("artifact_id", context_dict.pop("artifact", None)),
        annotator_id=context_dict.pop("annotator_id", context_dict.pop("annotator", None)),
        replica_id=context_dict.pop("replica_id", context_dict.pop("replica", None)),
        application_id=context_dict.pop("application_id", context_dict.pop("application", None)),
        orchestrator_id=context_dict.pop("orchestrator_id", context_dict.pop("orchestrator", None)),
        machine_id=context_dict.pop("machine_id", context_dict.pop("machine", None)),
        component_id=context_dict.pop("component_id", context_dict.pop("component", None)),
        pipeline_run_id=context_dict.pop("pipeline_run_id", context_dict.pop("pipeline_run", None)),
    )
