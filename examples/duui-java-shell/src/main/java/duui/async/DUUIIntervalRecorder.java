package duui.async;

import java.time.Duration;
import java.util.Objects;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

public abstract class DUUIIntervalRecorder implements DUUITracker {
    private final Duration interval;
    private DUUIPhase phase;
    private ScheduledExecutorService executor;
    private ScheduledFuture<?> task;

    protected DUUIIntervalRecorder(Duration interval) {
        this.interval = Objects.requireNonNull(interval, "interval");
    }

    @Override
    public final void init(DUUIPhase phase) {
        this.phase = Objects.requireNonNull(phase, "phase");
    }

    @Override
    public final void start() {
        executor = Executors.newSingleThreadScheduledExecutor();
        task = executor.scheduleAtFixedRate(
                () -> record(phase),
                0,
                interval.toMillis(),
                TimeUnit.MILLISECONDS
        );
    }

    @Override
    public final void stop() {
        if (task != null) {
            task.cancel(false);
        }
        if (executor != null) {
            executor.shutdownNow();
        }
    }

    protected abstract void record(DUUIPhase phase);
}
