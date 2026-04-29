package duui.async;

import java.util.Objects;
import java.util.concurrent.Future;

public final class DUUISubmission<T> {
    private final DUUIPhase phase;
    private final Future<T> future;

    public DUUISubmission(DUUIPhase phase, Future<T> future) {
        this.phase = Objects.requireNonNull(phase, "phase");
        this.future = Objects.requireNonNull(future, "future");
    }

    public DUUIPhase phase() {
        return phase;
    }

    public Future<T> future() {
        return future;
    }
}
