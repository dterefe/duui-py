# Events, Logging, Metrics, and Errors

When logging is enabled, `create_app` exposes one event endpoint:

```text
GET /v2/events
```

The endpoint is server-sent events. There is no polling route for the normal event protocol.

```bash
curl -N 'http://127.0.0.1:9714/v2/events?ttl_minutes=5'
```

Initial output:

```text
event: handshake
data: {"stream_id":"...","telemetry_protocol_version":"duui-otel-0.1",...}
```

The stream handshake is instance/session scoped. Use stream identifiers such as
`orchestrator_id`, `machine_id`, `component_id`, `replica_id`, and
`pipeline_run_id`. Task identifiers such as `artifact_id` and `request_id` are
attached to `/v1/process` events, not required for opening the stream.

## Logs

Annotators use the normal event logger for human-readable lifecycle and debug messages. It is a no-op when event logging is not configured.

```python
from duui_py.logging import get_event_logger_or_none


async def process(self, doc):
    logger = get_event_logger_or_none()
    if logger is not None:
        await logger.info("GNFinder processing started", extra={"text_length": len(text)})

    ...

    if logger is not None:
        await logger.info("GNFinder processing completed", extra={"matches": matches})
```

Example SSE log payload:

```text
event: log
data: {"type":"log","severity_text":"INFO","severity_number":9,"body":"GNFinder processing completed",...}
```

## Metrics

Annotators use the small `metrics` helper for counters, gauges, and timings.

```python
from time import time

from duui_py.metrics import metrics


async def process(self, doc):
    started = time()
    matches = 0

    for item in find_matches(doc):
        matches += 1
        yield item

    elapsed_ms = int((time() - started) * 1000)
    await metrics.count("gnfinder_taxon_matches", matches)
    await metrics.timing("gnfinder_processing_ms", elapsed_ms)
```

Timer form:

```python
async with metrics.timer("geonames_backend_lookup_ms"):
    response = await backend.lookup(payload)
```

Example SSE metric payload:

```text
event: metric
data: {"type":"metric","metric_type":"gauge","name":"gnfinder_taxon_matches","unit":"count","data_points":[...],...}
```

## Request Telemetry

Per-task telemetry is controlled through HTTP headers, not Lua parameters.

```http
X-DUUI-Telemetry: {"resource":["cpu","memory"],"stats":["duration","throughput","histogram"],"scopes":["global","orchestrator","component_replica"],"sample_interval_ms":500}
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
X-DUUI-Orchestrator-Id: orch-1
X-DUUI-Component-Id: taxonerd
X-DUUI-Replica-Id: replica-0
X-DUUI-Artifact-Id: doc-42
```

Default request telemetry records duration, throughput, error count, and latency
histograms for global/component/replica scopes. Resource polling is disabled
unless a request explicitly enables one or more of `cpu`, `memory`, `disk`, and
`network`.

The same observation can update multiple scoped histograms. This lets one shared
remote annotator report global latency and throughput while also reporting
per-orchestrator, per-pipeline-run, or per-component-replica statistics.

## Errors

Annotators raise HTTP-status based errors. The adapter logs them automatically and emits a DUUI error chunk.

```python
from duui_py.errors import unavailable, unprocessable


if not backend_url:
    unprocessable("GeoNames backend URL is required", parameter="backend_url")

try:
    response = backend.lookup(payload)
except TimeoutError:
    unavailable("GeoNames backend timed out", backend_url=backend_url)
```

The emitted error chunk carries the status and retryability:

```json
{
  "message": "GeoNames backend timed out",
  "status": 503,
  "title": "Service Unavailable",
  "retryable": true,
  "detail": {
    "backend_url": "http://127.0.0.1:9000"
  }
}
```

Default retryable statuses are `408`, `425`, `429`, `502`, `503`, and `504`.
