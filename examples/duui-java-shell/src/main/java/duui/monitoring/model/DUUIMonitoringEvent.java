package duui.monitoring.model;

import java.time.Instant;

public sealed interface DUUIMonitoringEvent permits DUUIEvent, DUUILog, DUUIMetric {
    Instant timestamp();

    String eventId();

    String name();
}
