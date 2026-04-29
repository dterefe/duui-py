package duui.monitoring.model;

import java.util.Map;
import java.util.Objects;
import java.time.Instant;
import java.util.UUID;

public record DUUILog(
    Instant timestamp,
    String eventId,
    String name,
    DUUIScope scope,
    Map<String, String> context,
    DUUILogLevel level,
    String message,
    Map<String, String> fields
) implements DUUIMonitoringEvent {
    public DUUILog {
        timestamp = timestamp == null ? Instant.now() : timestamp;
        eventId = eventId == null ? UUID.randomUUID().toString() : eventId;
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(level, "level");
        Objects.requireNonNull(message, "message");
        context = context == null ? Map.of() : Map.copyOf(context);
        fields = fields == null ? Map.of() : Map.copyOf(fields);
    }
}
