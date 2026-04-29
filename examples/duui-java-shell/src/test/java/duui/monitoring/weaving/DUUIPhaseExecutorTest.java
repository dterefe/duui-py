package duui.monitoring.weaving;

import duui.TestComposerSupport;
import duui.monitoring.logging.DUUIInMemoryEventEmitter;
import duui.monitoring.model.DUUIEvent;
import duui.monitoring.model.DUUIDispatchMode;
import duui.monitoring.model.DUUIPhaseMoment;
import duui.monitoring.model.DUUIStatus;
import duui.monitoring.telemetry.DUUITelemetryService;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class DUUIPhaseExecutorTest {
    @Test
    void emitsStartAndEndOnSuccess() throws Throwable {
        DUUITelemetryService service = new DUUITelemetryService(OpenTelemetrySdk.builder().build());
        TestComposerSupport.composerWith(service);
        DUUIInMemoryEventEmitter emitter = new DUUIInMemoryEventEmitter();
        service.registerEmitter(emitter);

        String value = DUUIPhaseExecutor.execute(
            "method",
            DUUIStatus.PROCESSING,
            DUUIDispatchMode.CPU,
            Map.of(),
            () -> "ok"
        );

        assertEquals("ok", value);
        assertEquals(DUUIPhaseMoment.START, ((DUUIEvent) emitter.events().get(0)).moment());
        assertEquals(DUUIPhaseMoment.END, ((DUUIEvent) emitter.events().get(1)).moment());
    }

    @Test
    void emitsFailureOnException() {
        DUUITelemetryService service = new DUUITelemetryService(OpenTelemetrySdk.builder().build());
        TestComposerSupport.composerWith(service);
        DUUIInMemoryEventEmitter emitter = new DUUIInMemoryEventEmitter();
        service.registerEmitter(emitter);

        assertThrows(
            IllegalStateException.class,
            () -> DUUIPhaseExecutor.execute(
                "method",
                DUUIStatus.PROCESSING,
                DUUIDispatchMode.IO,
                Map.of(),
                () -> {
                    throw new IllegalStateException("boom");
                }
            )
        );

        assertEquals(DUUIPhaseMoment.FAILURE, ((DUUIEvent) emitter.events().get(1)).moment());
    }
}
