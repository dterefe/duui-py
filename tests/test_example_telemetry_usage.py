import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ANNOTATORS = sorted((ROOT / "examples").glob("*/*_annotator.py"))


class ExampleTelemetryUsageTest(unittest.TestCase):
    def test_all_example_annotators_use_new_telemetry_facade(self):
        self.assertGreater(len(EXAMPLE_ANNOTATORS), 0)
        for path in EXAMPLE_ANNOTATORS:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("from duui_py.telemetry import telemetry", text)
                self.assertIn("await telemetry.", text)

    def test_old_logging_and_metrics_facades_are_not_used(self):
        forbidden = (
            "duui_py.metrics",
            "get_event_logger_or_none",
            "await logger.",
            "metrics.",
            "extra={",
        )
        for path in EXAMPLE_ANNOTATORS:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                for needle in forbidden:
                    self.assertNotIn(needle, text)


if __name__ == "__main__":
    unittest.main()
