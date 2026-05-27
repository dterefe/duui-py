import asyncio
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duui_py.logging.core import EventSink, LogLevel, configure_logger
from duui_py.logging.streaming import StreamConnection
from duui_py.telemetry import (
    Histogram,
    ScopeRegistry,
    TelemetryContext,
    TelemetryRequestConfig,
    parse_traceparent,
)


class MemorySink(EventSink):
    def __init__(self):
        self.events = []

    async def send(self, event):
        self.events.append(event)


class TelemetryTest(unittest.IsolatedAsyncioTestCase):
    async def test_log_event_is_otel_shaped(self):
        sink = MemorySink()
        logger = configure_logger(sinks=[sink], start_background_worker=False)

        await logger.info("hello", answer=42)

        self.assertEqual(len(sink.events), 1)
        event = sink.events[0]
        self.assertEqual(event.type, "log")
        self.assertEqual(event.severity_text, "INFO")
        self.assertEqual(event.severity_number, 9)
        self.assertEqual(event.body, "hello")
        self.assertIn("time_unix_nano", event.model_dump())
        self.assertIn("resource", event.model_dump())
        self.assertEqual(event.attributes["answer"], 42)

    async def test_count_metric_is_sum(self):
        sink = MemorySink()
        logger = configure_logger(sinks=[sink], start_background_worker=False)

        await logger.metric(
            "request", "duui.request.count", 3, "count", tags={"duui.scope": "global"}
        )

        event = sink.events[0]
        self.assertEqual(event.type, "metric")
        self.assertEqual(event.metric_type, "sum")
        self.assertEqual(event.data_points[0]["as_double"], 3.0)

    def test_telemetry_header_validation(self):
        config = TelemetryRequestConfig.from_header(
            json.dumps(
                {
                    "resource": ["cpu"],
                    "stats": ["duration", "histogram"],
                    "scopes": ["global", "orchestrator"],
                    "sample_interval_ms": 500,
                }
            )
        )

        self.assertEqual(config.resource, ("cpu",))
        self.assertEqual(config.stats, ("duration", "histogram"))
        self.assertEqual(config.scopes, ("global", "orchestrator"))
        self.assertEqual(config.sample_interval_ms, 500)

    def test_traceparent_parsing(self):
        trace_id, span_id = parse_traceparent(
            "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        )
        self.assertEqual(trace_id, "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(span_id, "00f067aa0ba902b7")

    def test_scope_registry(self):
        context = TelemetryContext(
            orchestrator_id="orch",
            component_id="component",
            replica_id="replica",
            telemetry=TelemetryRequestConfig(
                scopes=("global", "orchestrator", "component_replica")
            ),
        )

        scopes = ScopeRegistry.scopes(context)
        self.assertIn({"duui.scope": "global"}, scopes)
        self.assertIn(
            {"duui.scope": "orchestrator", "duui.orchestrator_id": "orch"}, scopes
        )
        self.assertIn(
            {
                "duui.scope": "component_replica",
                "duui.component_id": "component",
                "duui.replica_id": "replica",
            },
            scopes,
        )

    def test_histogram_summary(self):
        histogram = Histogram(buckets=(10.0, 100.0))
        histogram.record(5)
        histogram.record(50)
        histogram.record(500)
        snapshot = histogram.snapshot()

        self.assertEqual(snapshot["count"], 3)
        self.assertEqual(snapshot["bucket_counts"], [1, 1, 1])
        self.assertEqual(snapshot["p50"], 100.0)
        self.assertEqual(snapshot["p99"], 500)

    async def test_stream_handshake_is_session_scoped(self):
        stream = StreamConnection(
            stream_id="s1",
            identifiers={
                "orchestrator_id": "orch",
                "component_id": "component",
                "artifact_id": None,
            },
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            )
            + __import__("datetime").timedelta(seconds=30),
            max_queue_size=10,
        )

        events = stream.events()
        first = await events.__anext__()
        stream.close()
        await events.aclose()

        text = first.decode("utf-8")
        self.assertIn("event: handshake", text)
        payload = json.loads(text.split("data: ", 1)[1].strip())
        self.assertEqual(payload["stream_id"], "s1")
        self.assertIn("supported_scopes", payload)


if __name__ == "__main__":
    unittest.main()
