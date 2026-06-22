"""Shared backend lifecycle and HTTP utilities for DUUI-Py annotators.

Consolidates the duplicated subprocess management, HTTP connection pooling,
and backend readiness checking found in gnfinder-async and gazetteer-async.

Optimizations:
- Configurable connection pooling with keepalive
- HTTP/2 support for multiplexing (auto-detected, requires h2 package)
- Retry logic with exponential backoff for transient failures
- Health check integration
- Response streaming support
"""

from __future__ import annotations

import asyncio
import atexit
import json
import os
import shutil
import subprocess
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def _env_float(name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return max(minimum, float(raw))
    except ValueError:
        return default


# Detect HTTP/2 support lazily
_HTTP2_AVAILABLE: bool | None = None


def _http2_available() -> bool:
    global _HTTP2_AVAILABLE
    if _HTTP2_AVAILABLE is None:
        try:
            import h2  # noqa: F401
            _HTTP2_AVAILABLE = True
        except ImportError:
            _HTTP2_AVAILABLE = False
    return _HTTP2_AVAILABLE


class ManagedBackend:
    """Manages a subprocess backend lifecycle with async readiness polling.

    Eliminates the duplicated _BACKEND_LOCK/_BACKEND_PROCESS/_stop_local_backend
    patterns from gnfinder-async and gazetteer-async.
    """

    def __init__(
        self,
        binary_name: str,
        args: list[str],
        port: int,
        ping_path: str = "/api/v1/ping",
        startup_timeout: float = 120.0,
        poll_interval: float = 0.25,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
        ready_status_codes: set[int] | None = None,
        health_check_interval: float | None = None,
        readiness_timeout: float | None = None,
        health_timeout: float | None = None,
        stop_timeout: float | None = None,
        internal_max_connections: int | None = None,
        internal_max_keepalive_connections: int | None = None,
        internal_keepalive_expiry: float | None = None,
        internal_timeout: float | None = None,
        internal_connect_timeout: float | None = None,
    ):
        self._binary_name = binary_name
        self._args = args
        self._port = port
        self._ping_path = ping_path
        self._startup_timeout = startup_timeout
        self._poll_interval = poll_interval
        self._env = env
        self._cwd = cwd
        self._ready_status_codes = ready_status_codes or set(range(200, 300))

        self._lock = asyncio.Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self._url: str | None = None
        self._client: httpx.AsyncClient | None = None
        self._resolved_binary: str | None = None
        self._last_health_check: float = 0.0
        self._health_check_interval = (
            health_check_interval
            if health_check_interval is not None
            else _env_float("DUUI_BACKEND_HEALTH_CHECK_INTERVAL_SECONDS", 30.0)
        )
        self._readiness_timeout = (
            readiness_timeout
            if readiness_timeout is not None
            else _env_float("DUUI_BACKEND_READINESS_TIMEOUT_SECONDS", 1.0)
        )
        self._health_timeout = (
            health_timeout
            if health_timeout is not None
            else _env_float("DUUI_BACKEND_HEALTH_TIMEOUT_SECONDS", 2.0)
        )
        self._stop_timeout = (
            stop_timeout
            if stop_timeout is not None
            else _env_float("DUUI_BACKEND_STOP_TIMEOUT_SECONDS", 5.0)
        )
        self._internal_max_connections = (
            internal_max_connections
            if internal_max_connections is not None
            else _env_int("DUUI_BACKEND_INTERNAL_MAX_CONNECTIONS", 10)
        )
        self._internal_max_keepalive_connections = (
            internal_max_keepalive_connections
            if internal_max_keepalive_connections is not None
            else _env_int("DUUI_BACKEND_INTERNAL_MAX_KEEPALIVE_CONNECTIONS", 5)
        )
        self._internal_keepalive_expiry = (
            internal_keepalive_expiry
            if internal_keepalive_expiry is not None
            else _env_float("DUUI_BACKEND_INTERNAL_KEEPALIVE_EXPIRY_SECONDS", 60.0)
        )
        self._internal_timeout = (
            internal_timeout
            if internal_timeout is not None
            else _env_float("DUUI_BACKEND_INTERNAL_TIMEOUT_SECONDS", 5.0)
        )
        self._internal_connect_timeout = (
            internal_connect_timeout
            if internal_connect_timeout is not None
            else _env_float("DUUI_BACKEND_INTERNAL_CONNECT_TIMEOUT_SECONDS", 2.0)
        )

    def resolve_binary(
        self, parameter_value: str | None = None, extra_candidates: list[str] | None = None
    ) -> str | None:
        """Find the backend binary, checking parameter, PATH, and default."""
        for candidate in (
            parameter_value if parameter_value else None,
            *(extra_candidates or []),
            shutil.which(self._binary_name),
            self._binary_name,
        ):
            if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
                self._resolved_binary = candidate
                return candidate
        return None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            limits = httpx.Limits(
                max_connections=self._internal_max_connections,
                max_keepalive_connections=self._internal_max_keepalive_connections,
                keepalive_expiry=self._internal_keepalive_expiry,
            )
            self._client = httpx.AsyncClient(
                base_url=f"http://127.0.0.1:{self._port}",
                timeout=httpx.Timeout(self._internal_timeout, connect=self._internal_connect_timeout),
                limits=limits,
                http2=_http2_available(),
            )
        return self._client

    @property
    def url(self) -> str:
        return self._url or f"http://127.0.0.1:{self._port}"

    def _stop_process(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=self._stop_timeout)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=self._stop_timeout)

    async def health_check(self) -> bool:
        """Quick health check with caching to avoid hammering the backend."""
        now = asyncio.get_event_loop().time()
        if now - self._last_health_check < self._health_check_interval:
            return self._url is not None
        self._last_health_check = now
        try:
            response = await self.client.get(self._ping_path, timeout=self._health_timeout)
            return response.status_code in self._ready_status_codes
        except (httpx.HTTPError, httpx.TimeoutException, OSError):
            return False

    async def ensure_running(
        self,
        parameters: dict[str, Any] | None = None,
        force_binary: str | None = None,
    ) -> str:
        """Ensure the backend process is running and ready.

        Returns the backend base URL.
        """
        if self._url is not None:
            if await self._is_ready():
                return self._url
            self._url = None

        async with self._lock:
            if self._url is not None:
                if await self._is_ready():
                    return self._url
                self._url = None

            if self._url is None:
                if await self._is_ready():
                    self._url = f"http://127.0.0.1:{self._port}"
                    return self._url

                binary = force_binary or self._resolved_binary
                if binary is None:
                    binary = self.resolve_binary(
                        str(parameters.get(f"{self._binary_name}_binary") or "")
                        if parameters
                        else None
                    )
                if binary is None:
                    raise RuntimeError(f"{self._binary_name} binary not found")

                if self._process is None or self._process.poll() is not None:
                    cmd = [binary] + self._args
                    self._process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=self._env,
                        cwd=self._cwd,
                    )
                    atexit.register(self._stop_process)

                deadline = asyncio.get_event_loop().time() + self._startup_timeout
                attempts = 0
                while asyncio.get_event_loop().time() < deadline:
                    attempts += 1
                    if await self._is_ready():
                        self._url = f"http://127.0.0.1:{self._port}"
                        return self._url
                    await asyncio.sleep(self._poll_interval)

                raise RuntimeError(
                    f"{self._binary_name} backend did not become ready "
                    f"after {attempts} polls on port {self._port}"
                )

            return self._url

    async def _is_ready(self) -> bool:
        try:
            response = await self.client.get(self._ping_path, timeout=self._readiness_timeout)
            return response.status_code in self._ready_status_codes
        except (httpx.HTTPError, httpx.TimeoutException, OSError):
            return False

    async def shutdown(self) -> None:
        atexit.unregister(self._stop_process)
        self._stop_process()
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._url = None
        self._process = None


# ---------------------------------------------------------------------------
# Shared HTTP connection pool with keepalive, HTTP/2, retry, and health checks
# ---------------------------------------------------------------------------
_POOL_LOCK = asyncio.Lock()
_POOL_REFCOUNT: dict[str, int] = {}
_POOL_CLIENTS: dict[str, httpx.AsyncClient] = {}


async def _acquire_client(
    base_url: str,
    timeout: float = 120.0,
    http2: bool | None = None,
    max_connections: int | None = None,
    max_keepalive_connections: int | None = None,
    keepalive_expiry: float | None = None,
    connect_timeout: float | None = None,
    pool_timeout: float | None = None,
) -> httpx.AsyncClient:
    """Acquire a cached httpx client for the given base URL.

    Uses a shared pool keyed by base_url so that multiple annotator instances
    (or multiple requests to the same backend) reuse connections automatically.

    HTTP/2 is auto-detected: enabled if the ``h2`` package is installed,
    falls back to HTTP/1.1 otherwise.
    """
    if http2 is None:
        http2 = _http2_available()

    key = base_url.rstrip("/")
    async with _POOL_LOCK:
        if key in _POOL_CLIENTS:
            client = _POOL_CLIENTS[key]
            _POOL_REFCOUNT[key] += 1
            return client

        limits = httpx.Limits(
            max_connections=max_connections
            if max_connections is not None
            else _env_int("DUUI_HTTP_MAX_CONNECTIONS", 50),
            max_keepalive_connections=max_keepalive_connections
            if max_keepalive_connections is not None
            else _env_int("DUUI_HTTP_MAX_KEEPALIVE_CONNECTIONS", 50),
            keepalive_expiry=keepalive_expiry
            if keepalive_expiry is not None
            else _env_float("DUUI_HTTP_KEEPALIVE_EXPIRY_SECONDS", 60.0),
        )
        client = httpx.AsyncClient(
            base_url=key,
            timeout=httpx.Timeout(
                timeout,
                connect=connect_timeout
                if connect_timeout is not None
                else _env_float("DUUI_HTTP_CONNECT_TIMEOUT_SECONDS", 10.0),
                pool=pool_timeout
                if pool_timeout is not None
                else _env_float("DUUI_HTTP_POOL_TIMEOUT_SECONDS", 5.0),
            ),
            limits=limits,
            http2=http2,
        )
        _POOL_CLIENTS[key] = client
        _POOL_REFCOUNT[key] = 1
        return client


async def _release_client(base_url: str) -> None:
    """Release a reference to a shared client, closing it when refcount reaches zero."""
    key = base_url.rstrip("/")
    async with _POOL_LOCK:
        if key not in _POOL_CLIENTS:
            return
        _POOL_REFCOUNT[key] -= 1
        if _POOL_REFCOUNT[key] <= 0:
            client = _POOL_CLIENTS.pop(key)
            _POOL_REFCOUNT.pop(key)
            try:
                await client.aclose()
            except Exception:
                pass


async def shutdown_all_clients() -> None:
    """Close all pooled HTTP clients (call during app shutdown)."""
    async with _POOL_LOCK:
        for key, client in _POOL_CLIENTS.items():
            try:
                await client.aclose()
            except Exception:
                pass
        _POOL_CLIENTS.clear()
        _POOL_REFCOUNT.clear()


class ManagedHttpPool:
    """Optimized HTTP connection pool with keepalive, HTTP/2, retry, and health checks.

    Uses a global shared pool keyed by base_url so connections are reused
    across requests and annotator instances. Provides:
    - Connection reuse with configurable keepalive
    - HTTP/2 multiplexing
    - Retry with exponential backoff (configurable)
    - Response streaming via query_stream()
    - Backend health check
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 120.0,
        http2: bool | None = None,
        retries: int | None = None,
        backoff_base: float | None = None,
        max_connections: int | None = None,
        max_keepalive_connections: int | None = None,
        keepalive_expiry: float | None = None,
        connect_timeout: float | None = None,
        pool_timeout: float | None = None,
        health_timeout: float | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        # Auto-detect HTTP/2 if not specified
        self._http2 = _http2_available() if http2 is None else http2
        self._retries = retries if retries is not None else _env_int("DUUI_HTTP_RETRIES", 2, minimum=0)
        self._backoff_base = (
            backoff_base
            if backoff_base is not None
            else _env_float("DUUI_HTTP_BACKOFF_BASE_SECONDS", 0.5)
        )
        self._max_connections = max_connections
        self._max_keepalive_connections = max_keepalive_connections
        self._keepalive_expiry = keepalive_expiry
        self._connect_timeout = connect_timeout
        self._pool_timeout = pool_timeout
        self._health_timeout = (
            health_timeout
            if health_timeout is not None
            else _env_float("DUUI_HTTP_HEALTH_TIMEOUT_SECONDS", 5.0)
        )
        self._acquired = False

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily acquire a shared client on first use."""
        if not self._acquired:
            self._client = await _acquire_client(
                self._base_url,
                timeout=self._timeout,
                http2=self._http2,
                max_connections=self._max_connections,
                max_keepalive_connections=self._max_keepalive_connections,
                keepalive_expiry=self._keepalive_expiry,
                connect_timeout=self._connect_timeout,
                pool_timeout=self._pool_timeout,
            )
            self._acquired = True
        return self._client  # type: ignore[has-type]

    async def query(
        self,
        path: str,
        payload: dict[str, object],
        retries: int | None = None,
    ) -> Any:
        """POST a JSON payload to the backend with automatic retry on transient failures.

        Retries with exponential backoff: 0.5s, 1s, then raises on 3rd failure.
        """
        client = await self._ensure_client()
        last_exc: Exception | None = None

        retry_count = self._retries if retries is None else retries
        for attempt in range(retry_count + 1):
            try:
                response = await client.post(path, json=payload)
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as exc:
                last_exc = exc
                # Don't retry 4xx client errors (except 408/429)
                if isinstance(exc, httpx.HTTPStatusError):
                    status = exc.response.status_code
                    if status not in (408, 429, 502, 503, 504):
                        raise
                if attempt < retry_count:
                    wait = self._backoff_base * (2 ** attempt)
                    await asyncio.sleep(wait)
                else:
                    raise
        # Should not reach here, but satisfy type-checker
        raise RuntimeError("Query failed after all retries") from last_exc

    async def query_stream(
        self,
        path: str,
        payload: dict[str, object],
    ) -> AsyncIterator[dict[str, Any]]:
        """POST JSON to the backend and yield parsed chunks as they arrive.

        Uses httpx streaming under the hood to start processing the response
        incrementally rather than buffering the entire response body.
        """
        client = await self._ensure_client()
        async with client.stream("POST", path, json=payload) as response:
            response.raise_for_status()
            buffer = b""
            async for chunk in response.aiter_bytes():
                buffer += chunk
                # Attempt to parse partial JSON incrementally
                # For most backends, the full JSON arrives at once,
                # but this handles chunked transfer encoding gracefully.
                try:
                    data = json.loads(buffer)
                    yield data
                    buffer = b""
                except json.JSONDecodeError:
                    pass  # Need more chunks
            # If there's remaining data, try parsing it
            if buffer:
                try:
                    data = json.loads(buffer)
                    yield data
                except json.JSONDecodeError:
                    pass

    async def health(self, ping_path: str = "/api/v1/ping") -> bool:
        """Check if the backend is healthy."""
        try:
            client = await self._ensure_client()
            resp = await client.get(ping_path, timeout=self._health_timeout)
            return resp.status_code < 500
        except Exception:
            return False

    async def close(self) -> None:
        """Release the pooled client reference (does NOT close the TCP connection)."""
        if self._acquired:
            await _release_client(self._base_url)
            self._acquired = False
