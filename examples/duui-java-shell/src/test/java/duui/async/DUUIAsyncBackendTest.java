package duui.async;

import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

final class DUUIAsyncBackendTest {
    @Test
    void annotatedParentMethodAnchorsNormalNestedAnnotatedMethodCalls() {
        try (DUUIOrchestrator orchestrator = new DUUIOrchestrator()) {
            orchestrator.runtime().configuration().apply(new DUUIConfigurationPatch(
                    new DUUIResolvedConfiguration(
                            new DUUIMetadata(),
                            new DUUIExecutionPlan(
                                    DUUIExecutionMode.PLATFORM,
                                    DUUIScopeMode.CONCURRENT,
                                    DUUIOutsideScopeBehavior.THROW,
                                    null
                            ),
                            List.of(),
                            List.of(
                                    DUUIPhaseLifecycleTracker::new,
                                    DUUIPrometheusPhaseTracker::new,
                                    DUUIJfrPhaseTracker::new,
                                    () -> new DUUIOshiCpuRecorder(Duration.ofMillis(20))
                            )
                    ),
                    null,
                    null,
                    null,
                    null,
                    null
            ));
            BuildLikeFlow flow = new BuildLikeFlow();

            flow.build();

            DUUIPhase build = orchestrator.runtime().registry().requirePhaseNamed("build");
            waitUntil(build::active);

            assertEquals(DUUILifecycle.ACTIVE, build.lifecycle());
            assertTrue(build.trackerState().prometheus().isStarted());
            assertTrue(build.trackerState().jfr().isStarted());

            waitUntil(() -> !orchestrator.runtime().registry().phasesNamed("prepare").isEmpty());
            waitUntil(() -> !orchestrator.runtime().registry().phasesNamed("compile").isEmpty());
            DUUIPhase prepare = orchestrator.runtime().registry().requirePhaseNamed("prepare");
            DUUIPhase compile = orchestrator.runtime().registry().requirePhaseNamed("compile");

            waitUntil(() -> build.lifecycle() == DUUILifecycle.TERMINAL);

            assertSame(build, prepare.parent());
            assertSame(build, compile.parent());
            assertEquals(List.of(prepare, compile), build.subphases());
            assertEquals(List.of(build), orchestrator.runtime().registry().rootPhases());
            assertEquals(List.of(build, prepare, compile), orchestrator.runtime().registry().phasesFor(flow));
            assertTrue(build.entities().contains(flow));
            assertEquals(DUUILifecycle.TERMINAL, build.lifecycle());
            assertEquals(DUUILifecycle.TERMINAL, prepare.lifecycle());
            assertEquals(DUUILifecycle.TERMINAL, compile.lifecycle());
            assertEquals(List.of(
                    DUUILifecycle.CREATION,
                    DUUILifecycle.INACTIVE,
                    DUUILifecycle.ACTIVE,
                    DUUILifecycle.TERMINAL
            ), build.trackerState().lifecycle().states());
            assertTrue(build.trackerState().prometheus().isStopped());
            assertTrue(build.trackerState().jfr().isStopped());
            assertTrue(build.trackerState().oshiCpu().size() > 1);
        }
    }

    private static final class BuildLikeFlow implements DUUIEntity {
        private final DUUIId id = new DUUIId("entity", "build-like-flow", "flow-ulid");

        @Override
        public DUUIId duuiId() {
            return id;
        }

        @Async(name = "build")
        void build() {
            sleep(150);
            prepare();
            compile();
            sleep(150);
        }

        @Async(name = "prepare")
        void prepare() {
            sleep(100);
        }

        @Async(name = "compile")
        void compile() {
            sleep(100);
        }

        private void sleep(long millis) {
            try {
                Thread.sleep(millis);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new DUUIRuntimeException(e);
            }
        }
    }

    private static void waitUntil(Check check) {
        long deadline = System.nanoTime() + Duration.ofSeconds(5).toNanos();
        while (System.nanoTime() < deadline) {
            if (check.ok()) {
                return;
            }
            try {
                Thread.sleep(10);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new DUUIRuntimeException(e);
            }
        }
        fail("condition was not reached");
    }

    @FunctionalInterface
    private interface Check {
        boolean ok();
    }
}
