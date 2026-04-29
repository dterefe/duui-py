package duui.monitoring.model;

import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

public record DUUIMetric(
    Instant timestamp,
    String eventId,
    String name,
    DUUIScope scope,
    Map<String, String> context,
    String category,
    double value,
    String unit,
    long intervalMillis,
    Map<String, String> tags
) implements DUUIMonitoringEvent {
    public DUUIMetric {
        timestamp = timestamp == null ? Instant.now() : timestamp;
        eventId = eventId == null ? UUID.randomUUID().toString() : eventId;
        Objects.requireNonNull(name, "name");
        context = context == null ? Map.of() : Map.copyOf(context);
        Objects.requireNonNull(category, "category");
        Objects.requireNonNull(unit, "unit");
        tags = tags == null ? Map.of() : Map.copyOf(tags);
    }
}
