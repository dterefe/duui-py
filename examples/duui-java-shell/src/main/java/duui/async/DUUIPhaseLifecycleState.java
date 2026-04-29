package duui.async;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

public final class DUUIPhaseLifecycleState {
    private Instant initializedAt;
    private Instant startedAt;
    private Instant stoppedAt;
    private List<DUUILifecycle> states = List.of();

    public synchronized void initializedAt(Instant initializedAt) {
        this.initializedAt = initializedAt;
    }

    public synchronized Instant initializedAt() {
        return initializedAt;
    }

    public synchronized void startedAt(Instant startedAt) {
        this.startedAt = startedAt;
    }

    public synchronized Instant startedAt() {
        return startedAt;
    }

    public synchronized void stoppedAt(Instant stoppedAt) {
        this.stoppedAt = stoppedAt;
    }

    public synchronized Instant stoppedAt() {
        return stoppedAt;
    }

    public synchronized void states(List<DUUILifecycle> states) {
        this.states = List.copyOf(states);
    }

    public synchronized List<DUUILifecycle> states() {
        return new ArrayList<>(states);
    }
}
