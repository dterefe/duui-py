package duui.monitoring.telemetry;

import java.time.Duration;

public interface DUUIPollingTracker extends DUUITracker {
    Duration interval();

    void poll(DUUIPhaseSession session);
}
