package duui.async;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

public final class DUUIPhase implements DUUIEntity {
    private final DUUIId id;
    private final DUUIPhase parent;
    private final Set<DUUIEntity> entities;
    private final List<DUUIPhase> subphases = new ArrayList<>();
    private final List<DUUIPhaseTransition> transitions = Collections.synchronizedList(new ArrayList<>());
    private final DUUIPhaseTrackerState trackerState = new DUUIPhaseTrackerState();
    private DUUILifecycle lifecycle = DUUILifecycle.CREATION;

    public DUUIPhase(DUUIId id, DUUIPhase parent, Set<DUUIEntity> entities) {
        this.id = Objects.requireNonNull(id, "id");
        this.parent = parent;
        this.entities = new LinkedHashSet<>(Objects.requireNonNull(entities, "entities"));
        transitions.add(new DUUIPhaseTransition(DUUILifecycle.CREATION, Instant.now()));
    }

    @Override
    public DUUIId duuiId() {
        return id;
    }

    public DUUIPhase parent() {
        return parent;
    }

    public Set<DUUIEntity> entities() {
        return Set.copyOf(entities);
    }

    public List<DUUIPhase> subphases() {
        return List.copyOf(subphases);
    }

    public DUUILifecycle lifecycle() {
        return lifecycle;
    }

    public boolean active() {
        return lifecycle == DUUILifecycle.ACTIVE;
    }

    public List<DUUIPhaseTransition> transitions() {
        synchronized (transitions) {
            return List.copyOf(transitions);
        }
    }

    public DUUIPhaseTrackerState trackerState() {
        return trackerState;
    }

    public void addSubphase(DUUIPhase phase) {
        subphases.add(Objects.requireNonNull(phase, "phase"));
    }

    public void transition(DUUILifecycle next) {
        lifecycle = Objects.requireNonNull(next, "next");
        transitions.add(new DUUIPhaseTransition(next, Instant.now()));
    }
}
