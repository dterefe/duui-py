package duui.runtime;

import duui.monitoring.telemetry.DUUITelemetryService;
import duui.pipeline.DUUIPipeline;

import java.util.Objects;

public final class DUUIComposer {
    private final DUUIRuntime runtime;
    private final DUUIPipeline pipeline;
    private final DUUIWorker worker;

    public DUUIComposer(DUUIPipeline pipeline) {
        this.pipeline = Objects.requireNonNull(pipeline, "pipeline");
        this.runtime = new DUUIRuntime(this);
        this.runtime.installService(DUUITelemetryService.class, new DUUITelemetryService());
        this.worker = DUUIWorker.main(this, Thread.currentThread());
        this.pipeline.attach(this);
    }

    public DUUIRuntime runtime() {
        return runtime;
    }

    public DUUIPipeline pipeline() {
        return pipeline;
    }

    public DUUIWorker worker() {
        return worker;
    }
}
