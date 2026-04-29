package duui.monitoring.telemetry;

import duui.monitoring.model.DUUIDispatchMode;
import duui.monitoring.model.DUUIScope;
import duui.monitoring.model.DUUIStatus;
import io.opentelemetry.api.trace.Span;

import java.util.List;
import java.util.Objects;
import java.util.concurrent.ScheduledFuture;

public final class DUUIPhaseSession {
    private final String name;
    private final DUUIStatus status;
    private final DUUIDispatchMode dispatchMode;
    private final DUUIScope scope;
    private final Span span;
    private final List<DUUITracker> trackers;
    private final List<ScheduledFuture<?>> pollingTasks;

    public DUUIPhaseSession(
        String name,
        DUUIStatus status,
        DUUIDispatchMode dispatchMode,
        DUUIScope scope,
        Span span,
        List<DUUITracker> trackers,
        List<ScheduledFuture<?>> pollingTasks
    ) {
        this.name = Objects.requireNonNull(name, "name");
        this.status = Objects.requireNonNull(status, "status");
        this.dispatchMode = Objects.requireNonNull(dispatchMode, "dispatchMode");
        this.scope = Objects.requireNonNull(scope, "scope");
        this.span = Objects.requireNonNull(span, "span");
        this.trackers = List.copyOf(trackers);
        this.pollingTasks = List.copyOf(pollingTasks);
    }

    public String name() {
        return name;
    }

    public DUUIStatus status() {
        return status;
    }

    public DUUIDispatchMode dispatchMode() {
        return dispatchMode;
    }

    public DUUIScope scope() {
        return scope;
    }

    public Span span() {
        return span;
    }

    List<DUUITracker> trackers() {
        return trackers;
    }

    List<ScheduledFuture<?>> pollingTasks() {
        return pollingTasks;
    }
}
