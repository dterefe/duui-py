package duui;

import duui.pipeline.DUUIPipeline;
import duui.runtime.DUUIComposer;

public final class TestComposerSupport {
    private TestComposerSupport() {
    }

    public static DUUIComposer composer() {
        return new DUUIComposer(
            new DUUIPipeline()
                .add(new duui.pipeline.DUUISourceCheckpoint("source", null))
                .add(new duui.pipeline.DUUITargetCheckpoint("target"))
        );
    }

    public static DUUIComposer composerWith(duui.monitoring.telemetry.DUUITelemetryService telemetryService) {
        DUUIComposer composer = composer();
        composer.runtime().installService(duui.monitoring.telemetry.DUUITelemetryService.class, telemetryService);
        return composer;
    }
}
