from __future__ import annotations

from http import HTTPStatus
from typing import Any

from duui_py.logging.core import get_event_logger_or_none
from duui_py.models import DuuiError

RETRYABLE_STATUSES = {408, 425, 429, 502, 503, 504}


class DuuiHttpError(Exception):
    def __init__(
        self,
        status_code: int,
        message: str | None = None,
        *,
        retryable: bool | None = None,
        retry_after: int | None = None,
        detail: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ):
        self.status_code = int(status_code)
        self.message = message or _status_phrase(self.status_code)
        self.retryable = self.status_code in RETRYABLE_STATUSES if retryable is None else retryable
        self.retry_after = retry_after
        self.detail = detail or {}
        self.cause = cause
        super().__init__(self.message)

    @property
    def title(self) -> str:
        return _status_phrase(self.status_code)

    def to_duui_error(self) -> DuuiError:
        return DuuiError(
            message=self.message,
            status=self.status_code,
            title=self.title,
            retryable=self.retryable,
            retry_after=self.retry_after,
            detail=self.detail,
        )


def _status_phrase(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "DUUI error"


def fail(
    status_code: int,
    message: str | None = None,
    *,
    retryable: bool | None = None,
    retry_after: int | None = None,
    **detail: Any,
) -> None:
    raise DuuiHttpError(
        status_code,
        message,
        retryable=retryable,
        retry_after=retry_after,
        detail={k: v for k, v in detail.items() if v is not None},
    )


def bad_request(message: str, **detail: Any) -> None:
    fail(400, message, **detail)


def unauthorized(message: str, **detail: Any) -> None:
    fail(401, message, **detail)


def forbidden(message: str, **detail: Any) -> None:
    fail(403, message, **detail)


def not_found(message: str, **detail: Any) -> None:
    fail(404, message, **detail)


def conflict(message: str, **detail: Any) -> None:
    fail(409, message, **detail)


def unprocessable(message: str, **detail: Any) -> None:
    fail(422, message, **detail)


def too_many_requests(message: str, *, retry_after: int | None = None, **detail: Any) -> None:
    fail(429, message, retry_after=retry_after, **detail)


def internal_error(message: str = "Internal annotator error", **detail: Any) -> None:
    fail(500, message, **detail)


def bad_gateway(message: str, **detail: Any) -> None:
    fail(502, message, **detail)


def unavailable(message: str, *, retry_after: int | None = None, **detail: Any) -> None:
    fail(503, message, retry_after=retry_after, **detail)


def timeout(message: str, **detail: Any) -> None:
    fail(504, message, **detail)


async def log_duui_error(error: DuuiHttpError, *, operation: str | None = None) -> None:
    logger = get_event_logger_or_none()
    if logger is None:
        return
    extra = {
        "status": error.status_code,
        "title": error.title,
        "retryable": error.retryable,
        "detail": error.detail,
    }
    if error.retry_after is not None:
        extra["retry_after"] = error.retry_after
    if operation:
        extra["operation"] = operation
    await logger.error_event(
        error_type=str(error.status_code),
        message=error.message,
        extra=extra,
    )


def wrap_exception(exc: BaseException, *, message: str = "Internal annotator error") -> DuuiHttpError:
    return DuuiHttpError(
        500,
        message,
        detail={"exception_type": type(exc).__name__},
        cause=exc,
    )
