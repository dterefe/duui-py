package duui.async;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

public final class DUUIPhaseLifecycleTracker implements DUUITracker {
    private DUUIPhase phase;

    @Override
    public void init(DUUIPhase phase) {
        this.phase = phase;
        phase.trackerState().lifecycle().initializedAt(Instant.now());
    }

    @Override
    public void start() {
        phase.trackerState().lifecycle().startedAt(Instant.now());
    }

    @Override
    public void stop() {
        phase.trackerState().lifecycle().stoppedAt(Instant.now());
        List<DUUILifecycle> states = new ArrayList<>();
        for (DUUIPhaseTransition transition : phase.transitions()) {
            states.add(transition.lifecycle());
        }
        phase.trackerState().lifecycle().states(states);
    }
}
