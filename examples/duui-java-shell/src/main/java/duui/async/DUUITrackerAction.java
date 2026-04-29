package duui.async;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public final class DUUITrackerAction implements DUUIWrapperAction {
    private final List<DUUITrackerFactory> factories;
    private final Map<DUUIId, List<DUUITracker>> trackers = new ConcurrentHashMap<>();

    public DUUITrackerAction(List<DUUITrackerFactory> factories) {
        this.factories = List.copyOf(Objects.requireNonNull(factories, "factories"));
    }

    @Override
    public void before(DUUIInvocation invocation, DUUIPhase phase) {
        List<DUUITracker> active = new ArrayList<>();
        for (DUUITrackerFactory factory : factories) {
            DUUITracker tracker = factory.create();
            tracker.init(phase);
            active.add(tracker);
            tracker.start();
        }
        trackers.put(phase.duuiId(), active);
    }

    @Override
    public void cleanup(DUUIInvocation invocation, DUUIPhase phase) {
        List<DUUITracker> active = trackers.remove(phase.duuiId());
        if (active == null) {
            return;
        }
        for (int i = active.size() - 1; i >= 0; i--) {
            active.get(i).stop();
        }
    }
}
