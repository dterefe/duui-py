package duui.async;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Objects;

public final class DUUIContext {
    private final DUUIWorker worker;
    private final Deque<DUUIPhase> phaseStack = new ArrayDeque<>();

    DUUIContext(DUUIWorker worker) {
        this.worker = Objects.requireNonNull(worker, "worker");
    }

    public DUUIWorker worker() {
        return worker;
    }

    public DUUIRuntime runtime() {
        return worker.runtime();
    }

    public DUUIPhase currentPhase() {
        return phaseStack.peek();
    }

    public List<DUUIPhase> phaseStack() {
        return List.copyOf(new ArrayList<>(phaseStack));
    }

    public void push(DUUIPhase phase) {
        Objects.requireNonNull(phase, "phase");
        phaseStack.push(phase);
    }

    public void pop(DUUIPhase phase) {
        DUUIPhase current = phaseStack.poll();
        if (current != phase) {
            throw new DUUIRuntimeException("corrupted DUUI phase stack");
        }
    }
}
