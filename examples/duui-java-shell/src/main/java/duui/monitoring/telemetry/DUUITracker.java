package duui.monitoring.telemetry;

public interface DUUITracker {
    default void start(DUUIPhaseSession session) {
    }

    default void stop(DUUIPhaseSession session) {
    }
}
