from __future__ import annotations

import contextvars
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict


class EventContext(BaseModel):
    """Context for request-scoped event logging."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    
    context: Dict[str, str] = {}
    request_id: Optional[str] = None
    artifact_id: Optional[str] = None
    annotator_id: Optional[str] = None
    replica_id: Optional[str] = None
    application_id: Optional[str] = None


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
        )
        set_event_context(new_context)


def parse_event_context_param(event_context_param: str) -> Dict[str, str]:
    """
    Parse the event-context query parameter into a dictionary.
    
    Expected format: "key1=value1,key2=value2,key3=value3"
    """
    if not event_context_param:
        return {}
    
    result = {}
    pairs = event_context_param.split(",")
    for pair in pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            result[key.strip()] = value.strip()
        else:
            # Treat as key with empty value
            result[pair.strip()] = ""
    
    return result


def create_event_context_from_request(
    event_context_param: Optional[str] = None,
    request_id: Optional[str] = None,
    **extra_context: str,
) -> EventContext:
    """
    Create an EventContext from request parameters.
    
    Args:
        event_context_param: The raw event-context query parameter value
        request_id: Optional request ID (could be from headers)
        **extra_context: Additional context key-value pairs
    
    Returns:
        EventContext instance
    """
    context_dict = {}
    
    # Parse event-context query parameter
    if event_context_param:
        context_dict.update(parse_event_context_param(event_context_param))
    
    # Add extra context
    context_dict.update(extra_context)
    
    # Extract known fields from context
    known_fields = {
        "request_id": request_id,
        "artifact_id": context_dict.pop("artifact", None),
        "annotator_id": context_dict.pop("annotator", None),
        "replica_id": context_dict.pop("replica", None),
        "application_id": context_dict.pop("application", None),
    }
    
    # Clean up known fields from context dict
    for field in ["artifact", "annotator", "replica", "application"]:
        context_dict.pop(field, None)
    
    # Use explicit values if provided, otherwise fall back to context dict
    final_request_id = known_fields["request_id"] or context_dict.pop("request_id", None)
    
    return EventContext(
        context=context_dict,
        request_id=final_request_id,
        artifact_id=known_fields["artifact_id"] or context_dict.pop("artifact_id", None),
        annotator_id=known_fields["annotator_id"] or context_dict.pop("annotator_id", None),
        replica_id=known_fields["replica_id"] or context_dict.pop("replica_id", None),
        application_id=known_fields["application_id"] or context_dict.pop("application_id", None),
    )