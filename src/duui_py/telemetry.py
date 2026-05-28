from __future__ import annotations

import asyncio
import functools
import inspect
import json
import os
import socket
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from collections.abc import AsyncIterator
from typing import Any, Awaitable, Callable, Literal, TypeVar, ParamSpec, cast
from uuid import uuid4

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore[assignment]

P = ParamSpec("P")
R = TypeVar("R")


TELEMETRY_PROTOCOL_VERSION = "duui-otel-0.1"
DEFAULT_HISTOGRAM_BUCKETS_MS = (
    1.0,
    2.0,
    5.0,
    10.0,
    25.0,
    50.0,
    75.0,
    100.0,
    150.0,
    250.0,
    500.0,
    750.0,
    1000.0,
    1500.0,
    2500.0,
    5000.0,
    10000.0,
)
SUPPORTED_RESOURCE_CATEGORIES = frozenset({"cpu", "memory", "disk", "network"})
SUPPORTED_STATS = frozenset({"duration", "throughput", "histogram"})
SUPPORTED_SCOPES = frozenset(
    {
        "global",
        "machine",
        "orchestrator",
        "pipeline_run",
        "component",
        "replica",
        "component_replica",
        "orchestrator_component",
        "request",
        "artifact",
    }
)
DEFAULT_SCOPES = ("global", "component", "replica")
HIGH_CARDINALITY_SCOPES = frozenset({"request", "artifact"})
_HOST_RESOURCE_ATTRIBUTES: dict[str, str] | None = None


def now_unix_nano() -> int:
    return time.time_ns()


def new_span_id() -> str:
    return uuid4().hex[:16]


def host_resource_attributes() -> dict[str, str]:
    global _HOST_RESOURCE_ATTRIBUTES
    if _HOST_RESOURCE_ATTRIBUTES is None:
        host_name = socket.gethostname()
        attrs = {
            "service.name": "duui-py-annotator",
            "host.name": host_name,
            "process.pid": str(os.getpid()),
            "telemetry.sdk.name": "duui-py",
            "telemetry.protocol.version": TELEMETRY_PROTOCOL_VERSION,
        }
        try:
            attrs["host.ip"] = socket.gethostbyname(host_name)
        except OSError:
            pass
        _HOST_RESOURCE_ATTRIBUTES = attrs
    return dict(_HOST_RESOURCE_ATTRIBUTES)


def emit_background(awaitable: Awaitable[Any]) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        close = getattr(awaitable, "close", None)
        if callable(close):
            close()
        return
    task = loop.create_task(awaitable)
    task.add_done_callback(_consume_background_exception)


def _consume_background_exception(task: asyncio.Task[Any]) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        return
    except Exception as exc:
        print(f"Error emitting telemetry event: {exc}")


def parse_traceparent(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    parts = value.strip().split("-")
    if len(parts) != 4:
        return None, None
    _, trace_id, span_id, _ = parts
    if len(trace_id) != 32 or len(span_id) != 16:
        return None, None
    try:
        int(trace_id, 16)
        int(span_id, 16)
    except ValueError:
        return None, None
    return trace_id, span_id


class TelemetryRequestConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    resource: tuple[str, ...] = ("cpu", "memory", "network")
    stats: tuple[str, ...] = ("duration", "throughput", "histogram")
    scopes: tuple[str, ...] = DEFAULT_SCOPES
    sample_interval_ms: int = Field(default=1000, ge=100, le=60000)
    emit: Literal["summary", "stream", "both"] = "summary"

    @classmethod
    def default(cls) -> "TelemetryRequestConfig":
        return cls()

    @classmethod
    def from_header(cls, value: str | None) -> "TelemetryRequestConfig":
        if value is None or not value.strip():
            return cls.default()
        try:
            raw = json.loads(value)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400, detail=f"invalid X-DUUI-Telemetry JSON: {exc}"
            ) from exc
        if not isinstance(raw, dict):
            raise HTTPException(
                status_code=400, detail="X-DUUI-Telemetry must be a JSON object"
            )

        data = dict(raw)
        if "resource" in data:
            data["resource"] = _validate_values(
                "resource", data["resource"], SUPPORTED_RESOURCE_CATEGORIES
            )
        if "stats" in data:
            data["stats"] = _validate_values("stats", data["stats"], SUPPORTED_STATS)
        if "scopes" in data:
            data["scopes"] = _validate_values(
                "scopes", data["scopes"], SUPPORTED_SCOPES
            )
        return cls.model_validate(data)


def _validate_values(
    field_name: str, value: object, allowed: frozenset[str]
) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, list | tuple | set):
        values = tuple(str(item) for item in value)
    else:
        raise HTTPException(
            status_code=400, detail=f"telemetry {field_name} must be a string or list"
        )
    invalid = sorted(set(values).difference(allowed))
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported telemetry {field_name}: {', '.join(invalid)}",
        )
    return tuple(values)


class TelemetryContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    context: dict[str, str] = Field(default_factory=dict)
    request_id: str | None = None
    artifact_id: str | None = None
    annotator_id: str | None = None
    replica_id: str | None = None
    application_id: str | None = None
    orchestrator_id: str | None = None
    machine_id: str | None = None
    component_id: str | None = None
    pipeline_run_id: str | None = None
    trace_id: str | None = None
    parent_span_id: str | None = None
    span_id: str | None = None
    tracestate: str | None = None
    telemetry: TelemetryRequestConfig = Field(
        default_factory=TelemetryRequestConfig.default
    )

    def otel_attributes(self) -> dict[str, str]:
        attrs = dict(self.context)
        for key in (
            "request_id",
            "artifact_id",
            "annotator_id",
            "replica_id",
            "application_id",
            "orchestrator_id",
            "machine_id",
            "component_id",
            "pipeline_run_id",
        ):
            value = getattr(self, key)
            if value:
                attrs[f"duui.{key}"] = value
        return attrs


def parse_event_context_param(event_context_param: str | None) -> dict[str, str]:
    if not event_context_param:
        return {}
    result: dict[str, str] = {}
    for pair in event_context_param.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            result[key.strip()] = value.strip()
        elif pair.strip():
            result[pair.strip()] = ""
    return result


def create_telemetry_context_from_request(
    request: Request,
    *,
    event_context_param: str | None = None,
) -> TelemetryContext:
    context_dict = parse_event_context_param(event_context_param)
    trace_id, parent_span_id = parse_traceparent(request.headers.get("traceparent"))
    telemetry = TelemetryRequestConfig.from_header(
        request.headers.get("x-duui-telemetry")
    )

    def pick(*names: str) -> str | None:
        for name in names:
            value = request.headers.get(name)
            if value:
                return value
        return None

    known = {
        "request_id": pick("x-request-id", "x-duui-request-id")
        or context_dict.pop("request_id", None),
        "artifact_id": pick("x-duui-artifact-id")
        or context_dict.pop("artifact_id", context_dict.pop("artifact", None)),
        "annotator_id": pick("x-duui-annotator-id")
        or context_dict.pop("annotator_id", context_dict.pop("annotator", None)),
        "replica_id": pick("x-duui-replica-id")
        or context_dict.pop("replica_id", context_dict.pop("replica", None)),
        "application_id": pick("x-duui-application-id")
        or context_dict.pop("application_id", context_dict.pop("application", None)),
        "orchestrator_id": pick("x-duui-orchestrator-id")
        or context_dict.pop("orchestrator_id", context_dict.pop("orchestrator", None)),
        "machine_id": pick("x-duui-machine-id")
        or context_dict.pop("machine_id", context_dict.pop("machine", None)),
        "component_id": pick("x-duui-component-id")
        or context_dict.pop("component_id", context_dict.pop("component", None)),
        "pipeline_run_id": pick("x-duui-pipeline-run-id")
        or context_dict.pop("pipeline_run_id", context_dict.pop("pipeline_run", None)),
    }

    return TelemetryContext(
        context=context_dict,
        trace_id=trace_id or uuid4().hex,
        parent_span_id=parent_span_id,
        span_id=new_span_id(),
        tracestate=request.headers.get("tracestate"),
        telemetry=telemetry,
        **known,
    )


def create_stream_identifiers_from_request(request: Request) -> dict[str, str | None]:
    return {
        "orchestrator_id": request.query_params.get("orchestrator_id"),
        "machine_id": request.query_params.get("machine_id"),
        "component_id": request.query_params.get("component_id"),
        "replica_id": request.query_params.get("replica_id"),
        "pipeline_run_id": request.query_params.get("pipeline_run_id"),
        "annotator_id": request.query_params.get("annotator_id"),
        "application_id": request.query_params.get("application_id"),
    }


class Histogram:
    def __init__(self, buckets: tuple[float, ...] = DEFAULT_HISTOGRAM_BUCKETS_MS):
        self.buckets = buckets
        self.counts = [0 for _ in buckets] + [0]
        self.count = 0
        self.sum = 0.0
        self.min: float | None = None
        self.max: float | None = None

    def record(self, value: float) -> None:
        self.count += 1
        self.sum += value
        self.min = value if self.min is None else min(self.min, value)
        self.max = value if self.max is None else max(self.max, value)
        for index, upper in enumerate(self.buckets):
            if value <= upper:
                self.counts[index] += 1
                return
        self.counts[-1] += 1

    def percentile(self, percentile: float) -> float:
        if self.count == 0:
            return 0.0
        rank = max(1, int((percentile / 100.0) * self.count + 0.999999))
        cumulative = 0
        for index, count in enumerate(self.counts):
            cumulative += count
            if cumulative >= rank:
                if index < len(self.buckets):
                    return self.buckets[index]
                return self.max or 0.0
        return self.max or 0.0

    def snapshot(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "sum": self.sum,
            "min": self.min or 0.0,
            "max": self.max or 0.0,
            "mean": self.sum / self.count if self.count else 0.0,
            "bucket_bounds": list(self.buckets) + ["+Inf"],
            "bucket_counts": list(self.counts),
            "p50": self.percentile(50),
            "p90": self.percentile(90),
            "p95": self.percentile(95),
            "p99": self.percentile(99),
            "p99_9": self.percentile(99.9),
        }


@dataclass
class ScopeAggregation:
    histogram: Histogram = field(default_factory=Histogram)
    count: int = 0
    error_count: int = 0
    started_monotonic: float = field(default_factory=time.monotonic)


class AggregationStore:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._store: dict[tuple[str, tuple[tuple[str, str], ...]], ScopeAggregation] = (
            {}
        )

    async def record(
        self,
        metric_name: str,
        duration_ms: float,
        scopes: list[dict[str, str]],
        *,
        error: bool,
    ) -> list[tuple[dict[str, str], ScopeAggregation]]:
        out: list[tuple[dict[str, str], ScopeAggregation]] = []
        async with self._lock:
            for attrs in scopes:
                key = (metric_name, tuple(sorted(attrs.items())))
                item = self._store.setdefault(key, ScopeAggregation())
                item.histogram.record(duration_ms)
                item.count += 1
                if error:
                    item.error_count += 1
                out.append((attrs, item))
        return out


aggregation_store = AggregationStore()


class ScopeRegistry:
    @staticmethod
    def scopes(context: TelemetryContext) -> list[dict[str, str]]:
        requested = set(context.telemetry.scopes)
        scopes: list[dict[str, str]] = []

        def add(scope: str, **attrs: str | None) -> None:
            if scope not in requested:
                return
            clean = {key: value for key, value in attrs.items() if value}
            if scope != "global" and not clean:
                return
            scopes.append({"duui.scope": scope, **clean})

        add("global")
        add("machine", **{"duui.machine_id": context.machine_id})
        add("orchestrator", **{"duui.orchestrator_id": context.orchestrator_id})
        add("pipeline_run", **{"duui.pipeline_run_id": context.pipeline_run_id})
        add(
            "component",
            **{"duui.component_id": context.component_id or context.annotator_id},
        )
        add("replica", **{"duui.replica_id": context.replica_id})
        add(
            "component_replica",
            **{
                "duui.component_id": context.component_id or context.annotator_id,
                "duui.replica_id": context.replica_id,
            },
        )
        add(
            "orchestrator_component",
            **{
                "duui.orchestrator_id": context.orchestrator_id,
                "duui.component_id": context.component_id or context.annotator_id,
            },
        )
        add("request", **{"duui.request_id": context.request_id})
        add("artifact", **{"duui.artifact_id": context.artifact_id})
        return scopes


class ResourceSampler:
    def __init__(self, context: TelemetryContext):
        self.context = context
        self.categories = set(context.telemetry.resource)
        self.interval_seconds = max(context.telemetry.sample_interval_ms / 1000.0, 0.1)
        self.samples: list[dict[str, Any]] = []
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._process = psutil.Process() if PSUTIL_AVAILABLE else None
        self._last_disk = self._disk_io()
        self._last_net = self._net_io()
        self._last_time = time.monotonic()

    def start(self) -> None:
        if not self.categories or not PSUTIL_AVAILABLE:
            return
        self._running = True
        self._collect()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> list[dict[str, Any]]:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.categories and PSUTIL_AVAILABLE:
            self._collect()
        return self.samples

    async def _loop(self) -> None:
        while self._running:
            await asyncio.sleep(self.interval_seconds)
            self._collect()

    def _collect(self) -> None:
        now = time.monotonic()
        interval_ms = int((now - self._last_time) * 1000)
        self._last_time = now
        if "cpu" in self.categories:
            self.samples.extend(self._cpu(interval_ms))
        if "memory" in self.categories:
            self.samples.extend(self._memory(interval_ms))
        if "disk" in self.categories:
            self.samples.extend(self._disk(interval_ms))
        if "network" in self.categories:
            self.samples.extend(self._network(interval_ms))

    def _metric(
        self,
        category: str,
        name: str,
        value: float,
        unit: str,
        interval_ms: int,
        **attrs: str,
    ) -> dict[str, Any]:
        return {
            "category": category,
            "name": name,
            "value": value,
            "unit": unit,
            "interval_ms": interval_ms,
            "attributes": attrs,
        }

    def _cpu(self, interval_ms: int) -> list[dict[str, Any]]:
        out = []
        if self._process is not None:
            out.append(
                self._metric(
                    "cpu",
                    "process.cpu.utilization",
                    float(self._process.cpu_percent(None)),
                    "percent",
                    interval_ms,
                    scope="process",
                )
            )
            times = self._process.cpu_times()
            out.append(
                self._metric(
                    "cpu",
                    "process.cpu.time.user",
                    float(times.user),
                    "seconds",
                    interval_ms,
                    scope="process",
                )
            )
            out.append(
                self._metric(
                    "cpu",
                    "process.cpu.time.system",
                    float(times.system),
                    "seconds",
                    interval_ms,
                    scope="process",
                )
            )
            try:
                ctx = self._process.num_ctx_switches()
                out.append(
                    self._metric(
                        "cpu",
                        "process.context_switches.voluntary",
                        float(ctx.voluntary),
                        "count",
                        interval_ms,
                        scope="process",
                    )
                )
                out.append(
                    self._metric(
                        "cpu",
                        "process.context_switches.involuntary",
                        float(ctx.involuntary),
                        "count",
                        interval_ms,
                        scope="process",
                    )
                )
            except Exception:
                pass
        out.append(
            self._metric(
                "cpu",
                "system.cpu.utilization",
                float(psutil.cpu_percent(None)),
                "percent",
                interval_ms,
                scope="system",
            )
        )
        try:
            one, five, fifteen = psutil.getloadavg()
            out.append(
                self._metric(
                    "cpu",
                    "system.load_average.1m",
                    float(one),
                    "load",
                    interval_ms,
                    scope="system",
                )
            )
            out.append(
                self._metric(
                    "cpu",
                    "system.load_average.5m",
                    float(five),
                    "load",
                    interval_ms,
                    scope="system",
                )
            )
            out.append(
                self._metric(
                    "cpu",
                    "system.load_average.15m",
                    float(fifteen),
                    "load",
                    interval_ms,
                    scope="system",
                )
            )
        except Exception:
            pass
        return out

    def _memory(self, interval_ms: int) -> list[dict[str, Any]]:
        out = []
        if self._process is not None:
            info = self._process.memory_info()
            out.append(
                self._metric(
                    "memory",
                    "process.memory.rss",
                    float(info.rss),
                    "bytes",
                    interval_ms,
                    scope="process",
                )
            )
            out.append(
                self._metric(
                    "memory",
                    "process.memory.vms",
                    float(info.vms),
                    "bytes",
                    interval_ms,
                    scope="process",
                )
            )
            try:
                full = self._process.memory_full_info()
                uss = getattr(full, "uss", None)
                if uss is not None:
                    out.append(
                        self._metric(
                            "memory",
                            "process.memory.uss",
                            float(uss),
                            "bytes",
                            interval_ms,
                            scope="process",
                        )
                    )
            except Exception:
                pass
        virtual = psutil.virtual_memory()
        swap = psutil.swap_memory()
        out.append(
            self._metric(
                "memory",
                "system.memory.used",
                float(virtual.used),
                "bytes",
                interval_ms,
                scope="system",
            )
        )
        out.append(
            self._metric(
                "memory",
                "system.memory.available",
                float(virtual.available),
                "bytes",
                interval_ms,
                scope="system",
            )
        )
        out.append(
            self._metric(
                "memory",
                "system.memory.utilization",
                float(virtual.percent),
                "percent",
                interval_ms,
                scope="system",
            )
        )
        out.append(
            self._metric(
                "memory",
                "system.swap.used",
                float(swap.used),
                "bytes",
                interval_ms,
                scope="system",
            )
        )
        out.append(
            self._metric(
                "memory",
                "system.swap.utilization",
                float(swap.percent),
                "percent",
                interval_ms,
                scope="system",
            )
        )
        return out

    def _disk(self, interval_ms: int) -> list[dict[str, Any]]:
        current = self._disk_io()
        out = []
        if current:
            for key, value in current.items():
                out.append(
                    self._metric(
                        "disk",
                        f"system.disk.{key}",
                        value,
                        "count" if key.endswith("count") else "bytes",
                        interval_ms,
                        scope="system",
                    )
                )
            self._last_disk = current
        try:
            usage = psutil.disk_usage("/")
            out.append(
                self._metric(
                    "disk",
                    "system.filesystem.utilization",
                    float(usage.percent),
                    "percent",
                    interval_ms,
                    scope="system",
                    mount="/",
                )
            )
            out.append(
                self._metric(
                    "disk",
                    "system.filesystem.used",
                    float(usage.used),
                    "bytes",
                    interval_ms,
                    scope="system",
                    mount="/",
                )
            )
        except Exception:
            pass
        return out

    def _network(self, interval_ms: int) -> list[dict[str, Any]]:
        current = self._net_io()
        out = []
        if current:
            for key, value in current.items():
                out.append(
                    self._metric(
                        "network",
                        f"system.network.{key}",
                        value,
                        "count" if not key.endswith("bytes") else "bytes",
                        interval_ms,
                        scope="system",
                    )
                )
            self._last_net = current
        return out

    def _disk_io(self) -> dict[str, float] | None:
        try:
            io = psutil.disk_io_counters()
            if io is None:
                return None
            return {
                "read_bytes": float(io.read_bytes),
                "write_bytes": float(io.write_bytes),
                "read_count": float(io.read_count),
                "write_count": float(io.write_count),
            }
        except Exception:
            return None

    def _net_io(self) -> dict[str, float] | None:
        try:
            io = psutil.net_io_counters()
            if io is None:
                return None
            return {
                "sent_bytes": float(io.bytes_sent),
                "received_bytes": float(io.bytes_recv),
                "sent_packets": float(io.packets_sent),
                "received_packets": float(io.packets_recv),
                "errors_in": float(io.errin),
                "errors_out": float(io.errout),
                "drops_in": float(io.dropin),
                "drops_out": float(io.dropout),
            }
        except Exception:
            return None


class TelemetryRecorder:
    def __init__(self, operation: str = "duui.process"):
        from duui_py.logging.context import get_event_context

        self.context = get_event_context() or TelemetryContext()
        self.operation = operation
        self.started_ns = now_unix_nano()
        self.started_monotonic = time.perf_counter()
        self.phase_ms: dict[str, float] = {}
        self.extra_attributes: dict[str, str] = {}
        self.extra_metrics: list[tuple[str, str, float, str, int, dict[str, str]]] = []
        self.sampler = ResourceSampler(self.context)

    async def start(self) -> None:
        self.sampler.start()

    def mark(self, name: str, elapsed_ms: float) -> None:
        self.phase_ms[name] = elapsed_ms

    def attributes(self, values: dict[str, str]) -> None:
        self.extra_attributes.update(values)

    def metrics(
        self, values: list[tuple[str, str, float, str, int, dict[str, str]]]
    ) -> None:
        self.extra_metrics.extend(values)

    async def finish(
        self, *, status_code: int = 200, error: BaseException | None = None
    ) -> None:
        from duui_py.logging.core import get_configured_event_logger

        logger = get_configured_event_logger()
        has_active_sinks = logger is not None and logger.has_active_sinks()
        resource_samples = await self.sampler.stop()
        if not has_active_sinks or logger is None:
            return
        duration_ms = (time.perf_counter() - self.started_monotonic) * 1000.0
        scopes = ScopeRegistry.scopes(self.context)
        is_error = error is not None or status_code >= 400

        for sample in resource_samples:
            emit_background(
                logger.metric(
                    sample["category"],
                    sample["name"],
                    sample["value"],
                    sample["unit"],
                    sample["interval_ms"],
                    {**sample["attributes"], **self.context.otel_attributes()},
                )
            )

        for category, name, value, unit, interval_ms, attrs in self.extra_metrics:
            emit_background(
                logger.metric(
                    category,
                    name,
                    value,
                    unit,
                    interval_ms,
                    {**attrs, **self.context.otel_attributes()},
                )
            )

        aggregates = await aggregation_store.record(
            "duui.request.duration", duration_ms, scopes, error=is_error
        )
        for scope_attrs, aggregate in aggregates:
            elapsed = max(time.monotonic() - aggregate.started_monotonic, 0.001)
            tags = {
                **scope_attrs,
                **self.context.otel_attributes(),
                "status_code": str(status_code),
            }
            if "duration" in self.context.telemetry.stats:
                emit_background(
                    logger.metric(
                        "request",
                        "duui.request.duration",
                        duration_ms,
                        "milliseconds",
                        int(duration_ms),
                        tags,
                    )
                )
            if "histogram" in self.context.telemetry.stats:
                emit_background(
                    logger.histogram(
                        "request",
                        "duui.request.duration.histogram",
                        aggregate.histogram.snapshot(),
                        "milliseconds",
                        tags,
                    )
                )
            if "throughput" in self.context.telemetry.stats:
                emit_background(
                    logger.metric(
                        "request",
                        "duui.request.throughput",
                        aggregate.count / elapsed,
                        "requests_per_second",
                        0,
                        tags,
                    )
                )
                emit_background(
                    logger.metric(
                        "request",
                        "duui.request.count",
                        float(aggregate.count),
                        "count",
                        0,
                        tags,
                    )
                )
                if aggregate.error_count:
                    emit_background(
                        logger.metric(
                            "request",
                            "duui.request.errors",
                            float(aggregate.error_count),
                            "count",
                            0,
                            tags,
                        )
                    )

        emit_background(
            logger.span(
                name=self.operation,
                start_time_unix_nano=self.started_ns,
                end_time_unix_nano=now_unix_nano(),
                status_code=status_code,
                attributes={
                    **self.context.otel_attributes(),
                    **{
                        f"duui.phase.{key}_ms": str(int(value))
                        for key, value in self.phase_ms.items()
                    },
                    **self.extra_attributes,
                },
            )
        )
        emit_background(
            logger.summary(
                name="duui.request.summary",
                attributes={
                    **self.context.otel_attributes(),
                    "status_code": str(status_code),
                    "duration_ms": str(int(duration_ms)),
                    **{
                        f"{key}_ms": str(int(value))
                        for key, value in self.phase_ms.items()
                    },
                    **self.extra_attributes,
                },
            )
        )


class Telemetry:
    async def log(self, level: str, message: str, **attributes: Any) -> None:
        from duui_py.logging.core import LogLevel, get_configured_event_logger

        logger = get_configured_event_logger()
        if logger is None or not logger.has_active_sinks():
            return
        normalized = LogLevel[level.upper()]
        emit_background(logger.log(normalized, message, **attributes))

    async def debug(self, message: str, **attributes: Any) -> None:
        await self.log("DEBUG", message, **attributes)

    async def trace(self, message: str, **attributes: Any) -> None:
        await self.log("TRACE", message, **attributes)

    async def info(self, message: str, **attributes: Any) -> None:
        await self.log("INFO", message, **attributes)

    async def warning(self, message: str, **attributes: Any) -> None:
        await self.log("WARNING", message, **attributes)

    async def error(self, message: str, **attributes: Any) -> None:
        await self.log("ERROR", message, **attributes)

    async def critical(self, message: str, **attributes: Any) -> None:
        await self.log("CRITICAL", message, **attributes)

    async def count(self, name: str, value: float = 1, **attributes: str) -> None:
        await self.metric("processing", name, value, "count", **attributes)

    async def gauge(
        self, name: str, value: float, unit: str = "value", **attributes: str
    ) -> None:
        await self.metric("processing", name, value, unit, **attributes)

    async def timing(
        self, name: str, elapsed_ms: int | float, **attributes: str
    ) -> None:
        await self.metric(
            "processing",
            name,
            float(elapsed_ms),
            "milliseconds",
            interval_ms=int(elapsed_ms),
            **attributes,
        )

    async def metric(
        self,
        category: str,
        name: str,
        value: float,
        unit: str,
        *,
        interval_ms: int = 0,
        **attributes: str,
    ) -> None:
        from duui_py.logging.core import get_configured_event_logger

        logger = get_configured_event_logger()
        if logger is None or not logger.has_active_sinks():
            return
        emit_background(
            logger.metric(category, name, value, unit, interval_ms, attributes)
        )

    async def histogram(
        self,
        category: str,
        name: str,
        histogram: dict[str, Any],
        unit: str = "milliseconds",
        **attributes: str,
    ) -> None:
        from duui_py.logging.core import get_configured_event_logger

        logger = get_configured_event_logger()
        if logger is None or not logger.has_active_sinks():
            return
        emit_background(
            logger.histogram(category, name, histogram, unit, attributes)
        )

    @asynccontextmanager
    async def timer(self, name: str, **attributes: str) -> AsyncIterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            await self.timing(name, elapsed_ms, **attributes)

    def timed(
        self,
        name: str,
        *,
        category: str = "processing",
        unit: str = "milliseconds",
        **attributes: str,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        def decorate(func: Callable[P, R]) -> Callable[P, R]:
            if inspect.isasyncgenfunction(func):
                @functools.wraps(func)
                async def async_iter_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                    started = time.perf_counter()
                    try:
                        async for value in cast(Any, func)(*args, **kwargs):
                            yield value
                    finally:
                        elapsed_ms = (time.perf_counter() - started) * 1000.0
                        await self.metric(
                            category,
                            name,
                            elapsed_ms,
                            unit,
                            interval_ms=int(elapsed_ms),
                            **attributes,
                        )

                return cast(Callable[P, R], async_iter_wrapper)

            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                    started = time.perf_counter()
                    try:
                        return await cast(Any, func)(*args, **kwargs)
                    finally:
                        elapsed_ms = (time.perf_counter() - started) * 1000.0
                        await self.metric(
                            category,
                            name,
                            elapsed_ms,
                            unit,
                            interval_ms=int(elapsed_ms),
                            **attributes,
                        )

                return cast(Callable[P, R], async_wrapper)

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                started = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed_ms = (time.perf_counter() - started) * 1000.0
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        pass
                    else:
                        loop.create_task(
                            self.metric(
                                category,
                                name,
                                elapsed_ms,
                                unit,
                                interval_ms=int(elapsed_ms),
                                **attributes,
                            )
                        )

            return sync_wrapper

        return decorate


telemetry = Telemetry()
