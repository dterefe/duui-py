package duui.monitoring.model;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DUUIEventTest {
    @Test
    void buildsPhaseEvent() {
        DUUIEvent event = DUUIEvent.phase(
            "serialize",
            DUUIStatus.SERIALIZING,
            DUUIPhaseMoment.START,
            DUUIDispatchMode.CPU,
            new DUUIScope("scope-1", "serialize", null, Map.of("k", "v")),
            Map.of("k", "v"),
            null
        );

        assertEquals(DUUIStatus.SERIALIZING, event.status());
        assertEquals(DUUIPhaseMoment.START, event.moment());
    }

    @Test
    void buildsStandaloneLogAndMetricTypes() {
        DUUILog log = new DUUILog(null, null, "logger", null, Map.of(), DUUILogLevel.INFO, "x", Map.of());
        DUUIMetric metric = new DUUIMetric(null, null, "cpu.percent", null, Map.of(), "cpu", 1.0, "percent", 0L, Map.of());

        assertEquals("logger", log.name());
        assertEquals("cpu.percent", metric.name());
    }
}
