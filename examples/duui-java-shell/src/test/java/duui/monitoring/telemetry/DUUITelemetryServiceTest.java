package duui.monitoring.telemetry;

import duui.TestComposerSupport;
import duui.monitoring.logging.DUUIInMemoryEventEmitter;
import duui.monitoring.model.DUUIEvent;
import duui.monitoring.model.DUUIDispatchMode;
import duui.monitoring.model.DUUIPhaseMoment;
import duui.monitoring.model.DUUIStatus;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.testing.exporter.InMemorySpanExporter;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import org.junit.jupiter.api.Test;

import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DUUITelemetryServiceTest {
    @Test
    void emitsPhaseLifecycleAndEndsSpan() {
        TestComposerSupport.composer();
        InMemorySpanExporter exporter = InMemorySpanExporter.create();
        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(exporter))
            .build();
        OpenTelemetrySdk openTelemetry = OpenTelemetrySdk.builder()
            .setTracerProvider(tracerProvider)
            .build();

        DUUITelemetryService service = new DUUITelemetryService(openTelemetry);
        DUUIInMemoryEventEmitter emitter = new DUUIInMemoryEventEmitter();
        service.registerEmitter(emitter);

        DUUIPhaseSession session = service.beginPhase("serialize", DUUIStatus.SERIALIZING, DUUIDispatchMode.CPU, Map.of());
        service.endPhase(session);

        assertEquals(2, emitter.events().size());
        assertEquals(DUUIPhaseMoment.START, ((DUUIEvent) emitter.events().get(0)).moment());
        assertEquals(DUUIPhaseMoment.END, ((DUUIEvent) emitter.events().get(1)).moment());
        assertEquals(1, exporter.getFinishedSpanItems().size());
    }

    @Test
    void activatesTrackers() {
        TestComposerSupport.composer();
        DUUITelemetryService service = new DUUITelemetryService(OpenTelemetrySdk.builder().build());
        AtomicInteger starts = new AtomicInteger();
        AtomicInteger stops = new AtomicInteger();
        service.registerTracker(new DUUITracker() {
            @Override
            public void start(DUUIPhaseSession session) {
                starts.incrementAndGet();
            }

            @Override
            public void stop(DUUIPhaseSession session) {
                stops.incrementAndGet();
            }
        });

        DUUIPhaseSession session = service.beginPhase("phase", DUUIStatus.RUNNING, DUUIDispatchMode.MIXED, Map.of());
        service.endPhase(session);

        assertEquals(1, starts.get());
        assertEquals(1, stops.get());
    }

    @Test
    void configReloadAffectsLaterScopes() {
        TestComposerSupport.composer();
        DUUITelemetryService service = new DUUITelemetryService(OpenTelemetrySdk.builder().build());
        DUUIInMemoryEventEmitter emitter = new DUUIInMemoryEventEmitter();
        service.registerEmitter(emitter);

        service.updateConfig(new DUUITelemetryConfig(false, true, true, Map.of()));
        DUUIPhaseSession session = service.beginPhase("phase", DUUIStatus.RUNNING, DUUIDispatchMode.IO, Map.of());
        service.endPhase(session);

        assertTrue(emitter.events().isEmpty());
    }
}
