package duui.async;

public final class DUUIPhaseTrackerState {
    private final DUUIPhaseLifecycleState lifecycle = new DUUIPhaseLifecycleState();
    private final DUUIOshiCpuSamples oshiCpu = new DUUIOshiCpuSamples();
    private final DUUIPrometheusPhaseState prometheus = new DUUIPrometheusPhaseState();
    private final DUUIJfrPhaseState jfr = new DUUIJfrPhaseState();

    public DUUIPhaseLifecycleState lifecycle() {
        return lifecycle;
    }

    public DUUIOshiCpuSamples oshiCpu() {
        return oshiCpu;
    }

    public DUUIPrometheusPhaseState prometheus() {
        return prometheus;
    }

    public DUUIJfrPhaseState jfr() {
        return jfr;
    }
}
