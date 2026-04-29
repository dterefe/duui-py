package duui.monitoring.model;

import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

public record DUUIEvent(
    Instant timestamp,
    String eventId,
    String name,
    DUUIStatus status,
    DUUIPhaseMoment moment,
    DUUIDispatchMode dispatchMode,
    DUUIScope scope,
    Map<String, String> context,
    String failureMessage
) implements DUUIMonitoringEvent {
    public DUUIEvent {
        timestamp = timestamp == null ? Instant.now() : timestamp;
        eventId = eventId == null ? UUID.randomUUID().toString() : eventId;
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(status, "status");
        Objects.requireNonNull(moment, "moment");
        context = context == null ? Map.of() : Map.copyOf(context);
    }

    public static DUUIEvent phase(
        String name,
        DUUIStatus status,
        DUUIPhaseMoment moment,
        DUUIDispatchMode dispatchMode,
        DUUIScope scope,
        Map<String, String> context,
        String failureMessage
    ) {
        return new DUUIEvent(
            Instant.now(),
            null,
            name,
            status,
            moment,
            dispatchMode,
            scope,
            context,
            failureMessage
        );
    }
}
