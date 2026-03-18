from __future__ import annotations

import asyncio
import functools
import sys
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, TypeVar
from uuid import uuid4

from duui_py.logging.core import get_event_logger, ErrorEvent, LogLevel


T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def log_errors(
    log_level: LogLevel = LogLevel.ERROR,
    include_stack_trace: bool = True,
    recovery_suggestion: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> Callable[[F], F]:
    """
    Decorator to catch and log exceptions from functions.
    
    Args:
        log_level: Log level for the error event
        include_stack_trace: Whether to include stack trace in error event
        recovery_suggestion: Optional recovery suggestion
        extra_context: Additional context to include with the error
    
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await _log_exception(
                    e,
                    func.__name__,
                    log_level,
                    include_stack_trace,
                    recovery_suggestion,
                    extra_context,
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Run in background since we can't await in sync function
                import asyncio
                asyncio.create_task(
                    _log_exception(
                        e,
                        func.__name__,
                        log_level,
                        include_stack_trace,
                        recovery_suggestion,
                        extra_context,
                    )
                )
                raise
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


async def _log_exception(
    exception: Exception,
    function_name: str,
    log_level: LogLevel,
    include_stack_trace: bool,
    recovery_suggestion: Optional[str],
    extra_context: Optional[Dict[str, Any]],
) -> None:
    """Log an exception as an error event."""
    logger = get_event_logger()
    
    stack_trace = None
    if include_stack_trace:
        stack_trace = "".join(traceback.format_exception(
            type(exception), exception, exception.__traceback__
        ))
    
    # Build extra context
    extra = extra_context or {}
    extra.update({
        "function": function_name,
        "exception_type": type(exception).__name__,
    })
    
    await logger.error_event(
        error_type=type(exception).__name__,
        message=str(exception),
        stack_trace=stack_trace,
        recovery_suggestion=recovery_suggestion,
        extra=extra,
    )
    
    # Also log as regular error for backward compatibility
    error_message = f"Error in {function_name}: {type(exception).__name__}: {exception}"
    await logger.error(error_message, extra=extra)


@contextmanager
def error_context(
    operation_name: str,
    log_level: LogLevel = LogLevel.ERROR,
    include_stack_trace: bool = True,
    recovery_suggestion: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None,
):
    """
    Context manager for scoped error handling.
    
    Usage:
        with error_context("processing_document"):
            # code that may raise exceptions
    
    Args:
        operation_name: Name of the operation for context
        log_level: Log level for errors
        include_stack_trace: Whether to include stack trace
        recovery_suggestion: Optional recovery suggestion
        extra_context: Additional context
    """
    try:
        yield
    except Exception as e:
        # Run in background since we can't await in context manager
        import asyncio
        asyncio.create_task(
            _log_exception(
                e,
                operation_name,
                log_level,
                include_stack_trace,
                recovery_suggestion,
                extra_context,
            )
        )
        raise


def log_exception(
    exception: Exception,
    operation_name: str,
    log_level: LogLevel = LogLevel.ERROR,
    include_stack_trace: bool = True,
    recovery_suggestion: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an exception immediately.
    
    This function can be called in exception handlers to log exceptions.
    It runs the logging in the background.
    
    Args:
        exception: The exception to log
        operation_name: Name of the operation where exception occurred
        log_level: Log level for the error
        include_stack_trace: Whether to include stack trace
        recovery_suggestion: Optional recovery suggestion
        extra_context: Additional context
    """
    import asyncio
    asyncio.create_task(
        _log_exception(
            exception,
            operation_name,
            log_level,
            include_stack_trace,
            recovery_suggestion,
            extra_context,
        )
    )


def log_error_message(
    message: str,
    error_type: str = "GenericError",
    operation_name: Optional[str] = None,
    log_level: LogLevel = LogLevel.ERROR,
    stack_trace: Optional[str] = None,
    recovery_suggestion: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an error message (without an exception).
    
    Useful for logging error conditions that don't raise exceptions.
    
    Args:
        message: Error message
        error_type: Type of error
        operation_name: Name of the operation
        log_level: Log level for the error
        stack_trace: Optional stack trace
        recovery_suggestion: Optional recovery suggestion
        extra_context: Additional context
    """
    import asyncio
    
    async def _log() -> None:
        logger = get_event_logger()
        
        extra = extra_context or {}
        if operation_name:
            extra["operation"] = operation_name
        
        await logger.error_event(
            error_type=error_type,
            message=message,
            stack_trace=stack_trace,
            recovery_suggestion=recovery_suggestion,
            extra=extra,
        )
        
        # Also log as regular error
        error_msg = f"{error_type}: {message}"
        if operation_name:
            error_msg = f"{operation_name}: {error_msg}"
        await logger.error(error_msg, extra=extra)
    
    asyncio.create_task(_log())