package duui.async;

import java.lang.reflect.Method;
import java.util.Objects;
import java.util.Set;

public final class DUUIPhaseFactory {
    private final DUUIUlids ulids = new DUUIUlids();

    public DUUIInvocation invocation(Class<?> ownerType, Method method, Async annotation, DUUIWorker worker, Set<DUUIEntity> entities) {
        return new DUUIInvocation(ownerType, method, annotation, worker, entities);
    }

    public DUUIPhase phase(DUUIInvocation invocation) {
        Objects.requireNonNull(invocation, "invocation");
        String phaseName = invocation.annotation().name();
        DUUIPhase parent = invocation.worker().context().currentPhase();
        DUUIPhase phase = new DUUIPhase(new DUUIId("phase", phaseName, ulids.next()), parent, invocation.entities());
        if (parent != null) {
            parent.addSubphase(phase);
        }
        return phase;
    }
}
