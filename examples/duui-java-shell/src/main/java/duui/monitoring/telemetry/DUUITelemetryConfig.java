package duui.monitoring.telemetry;

import java.util.Map;

public record DUUITelemetryConfig(
    boolean phaseEventsEnabled,
    boolean logsEnabled,
    boolean metricsEnabled,
    Map<String, String> properties
) {
    public DUUITelemetryConfig {
        properties = properties == null ? Map.of() : Map.copyOf(properties);
    }

    public static DUUITelemetryConfig standard() {
        return new DUUITelemetryConfig(true, true, true, Map.of());
    }
}
