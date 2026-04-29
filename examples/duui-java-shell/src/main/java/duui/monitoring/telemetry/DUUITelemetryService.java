package duui.monitoring.telemetry;

import duui.monitoring.logging.DUUICompositeEventEmitter;
import duui.monitoring.logging.DUUIEventEmitter;
import duui.monitoring.logging.DUUILogContext;
import duui.monitoring.logging.DUUILogger;
import duui.monitoring.model.DUUIDispatchMode;
import duui.monitoring.model.DUUIEvent;
import duui.monitoring.model.DUUIPhaseMoment;
import duui.monitoring.model.DUUIScope;
import duui.monitoring.model.DUUIStatus;
import duui.runtime.DUUIWorker;
import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.metrics.Meter;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

public final class DUUITelemetryService {
    private static final AtomicReference<DUUITelemetryService> CURRENT =
        new AtomicReference<>(new DUUITelemetryService(GlobalOpenTelemetry.get()));

    private final DUUICompositeEventEmitter emitter;
    private final CopyOnWriteArrayList<DUUITracker> trackers = new CopyOnWriteArrayList<>();
    private final AtomicReference<DUUITelemetryConfig> config = new AtomicReference<>(DUUITelemetryConfig.standard());
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
    private final OpenTelemetry openTelemetry;
    private final Tracer tracer;
    private final Meter meter;

    public DUUITelemetryService() {
        this(GlobalOpenTelemetry.get());
    }

    public DUUITelemetryService(OpenTelemetry openTelemetry) {
        this.openTelemetry = Objects.requireNonNull(openTelemetry, "openTelemetry");
        this.tracer = openTelemetry.getTracer("duui.monitoring");
        this.meter = openTelemetry.getMeter("duui.monitoring");
        this.emitter = new DUUICompositeEventEmitter(List.of());
    }

    public static DUUITelemetryService get() {
        if (DUUIWorker.currentOptional().isPresent()) {
            return DUUIWorker.current().runtime()
                .serviceOptional(DUUITelemetryService.class)
                .orElse(CURRENT.get());
        }
        return CURRENT.get();
    }

    public static void install(DUUITelemetryService service) {
        CURRENT.set(Objects.requireNonNull(service, "service"));
    }

    public void registerEmitter(DUUIEventEmitter eventEmitter) {
        emitter.register(eventEmitter);
    }

    public void unregisterEmitter(DUUIEventEmitter eventEmitter) {
        emitter.unregister(eventEmitter);
    }

    public void registerTracker(DUUITracker tracker) {
        trackers.add(Objects.requireNonNull(tracker, "tracker"));
    }

    public void unregisterTracker(DUUITracker tracker) {
        trackers.remove(tracker);
    }

    public void updateConfig(DUUITelemetryConfig newConfig) {
        config.set(Objects.requireNonNull(newConfig, "newConfig"));
    }

    public DUUITelemetryConfig config() {
        return config.get();
    }

    public Tracer tracer() {
        return tracer;
    }

    public Meter meter() {
        return meter;
    }

    public DUUILogger logger(String name) {
        return new DUUILogger(emitter, name);
    }

    public DUUIPhaseSession beginPhase(
        String name,
        DUUIStatus status,
        DUUIDispatchMode dispatchMode,
        Map<String, String> context
    ) {
        DUUIScope parent = DUUILogContext.currentScope().orElse(null);
        DUUIScope scope = new DUUIScope(
            UUID.randomUUID().toString(),
            name,
            parent == null ? null : parent.id(),
            context
        );

        Span span = tracer.spanBuilder(name)
            .setAttribute("duui.status", status.name())
            .setAttribute("duui.dispatch", dispatchMode.name())
            .startSpan();

        DUUILogContext.push(scope);

        if (config().phaseEventsEnabled()) {
            emitter.emit(DUUIEvent.phase(name, status, DUUIPhaseMoment.START, dispatchMode, scope, context, null));
        }

        List<DUUITracker> activeTrackers = List.copyOf(trackers);
        List<ScheduledFuture<?>> pollingTasks = new ArrayList<>();
        DUUIPhaseSession session = new DUUIPhaseSession(name, status, dispatchMode, scope, span, activeTrackers, pollingTasks);

        for (DUUITracker tracker : activeTrackers) {
            tracker.start(session);
            if (tracker instanceof DUUIPollingTracker pollingTracker) {
                Duration interval = pollingTracker.interval();
                ScheduledFuture<?> future = scheduler.scheduleAtFixedRate(
                    () -> pollingTracker.poll(session),
                    interval.toMillis(),
                    interval.toMillis(),
                    TimeUnit.MILLISECONDS
                );
                pollingTasks.add(future);
            }
        }

        return session;
    }

    public void endPhase(DUUIPhaseSession session) {
        finishPhase(session, null);
    }

    public void failPhase(DUUIPhaseSession session, Throwable error) {
        finishPhase(session, Objects.requireNonNull(error, "error"));
    }

    private void finishPhase(DUUIPhaseSession session, Throwable error) {
        for (ScheduledFuture<?> task : session.pollingTasks()) {
            task.cancel(true);
        }
        for (DUUITracker tracker : session.trackers()) {
            tracker.stop(session);
        }

        if (error == null) {
            if (config().phaseEventsEnabled()) {
                emitter.emit(
                    DUUIEvent.phase(
                        session.name(),
                        session.status(),
                        DUUIPhaseMoment.END,
                        session.dispatchMode(),
                        session.scope(),
                        session.scope().context(),
                        null
                    )
                );
            }
        } else {
            session.span().recordException(error);
            session.span().setStatus(StatusCode.ERROR, error.getMessage());
            if (config().phaseEventsEnabled()) {
                emitter.emit(
                    DUUIEvent.phase(
                        session.name(),
                        session.status(),
                        DUUIPhaseMoment.FAILURE,
                        session.dispatchMode(),
                        session.scope(),
                        session.scope().context(),
                        error.getMessage()
                    )
                );
            }
        }

        session.span().end();
        DUUILogContext.pop();
    }
}
