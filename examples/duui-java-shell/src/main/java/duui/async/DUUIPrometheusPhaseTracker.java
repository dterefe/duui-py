package duui.async;

import io.prometheus.metrics.core.metrics.Counter;

public final class DUUIPrometheusPhaseTracker implements DUUITracker {
    private static final Counter PHASE_STARTS = Counter.builder()
            .name("duui_phase_starts_total")
            .help("DUUI phase starts.")
            .labelNames("phase")
            .register();

    private static final Counter PHASE_STOPS = Counter.builder()
            .name("duui_phase_stops_total")
            .help("DUUI phase stops.")
            .labelNames("phase")
            .register();

    private DUUIPhase phase;

    @Override
    public void init(DUUIPhase phase) {
        this.phase = phase;
    }

    @Override
    public void start() {
        PHASE_STARTS.labelValues(phase.duuiId().name()).inc();
        phase.trackerState().prometheus().started();
    }

    @Override
    public void stop() {
        PHASE_STOPS.labelValues(phase.duuiId().name()).inc();
        phase.trackerState().prometheus().stopped();
    }
}
