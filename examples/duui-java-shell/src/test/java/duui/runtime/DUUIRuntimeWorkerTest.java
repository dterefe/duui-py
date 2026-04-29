package duui.runtime;

import duui.pipeline.DUUIPipeline;
import duui.pipeline.DUUITargetCheckpoint;
import duui.pipeline.DUUISourceCheckpoint;
import org.junit.jupiter.api.Test;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DUUIRuntimeWorkerTest {
    private static DUUIComposer composer() {
        return new DUUIComposer(new DUUIPipeline().add(new DUUISourceCheckpoint("source", null)).add(new DUUITargetCheckpoint("target")));
    }

    @Test
    void composerRegistersCurrentThreadAsMainWorker() {
        DUUIComposer composer = composer();
        assertNotNull(composer.worker());
        assertTrue(DUUIWorker.current() == composer.worker());
    }

    @Test
    void currentFailsOnUnregisteredThread() throws InterruptedException {
        CountDownLatch done = new CountDownLatch(1);
        AtomicBoolean failed = new AtomicBoolean(false);
        Thread thread = Thread.ofPlatform().start(() -> {
            try {
                assertThrows(IllegalStateException.class, DUUIWorker::current);
                failed.set(true);
            } finally {
                done.countDown();
            }
        });
        done.await(5, TimeUnit.SECONDS);
        thread.join();
        assertTrue(failed.get());
    }

    @Test
    void workerFactoriesPropagateContext() throws Exception {
        DUUIComposer composer = composer();
        composer.worker().pushScope(new duui.monitoring.model.DUUIScope("scope-1", "phase", null, java.util.Map.of()));
        CountDownLatch done = new CountDownLatch(2);
        AtomicBoolean platformOk = new AtomicBoolean(false);
        AtomicBoolean virtualOk = new AtomicBoolean(false);

        try (DUUIPlatformExecutor platform = composer.worker().platformExecutor(1, "platform");
             DUUIVirtualExecutor virtual = composer.worker().virtualExecutor("virtual")) {
            platform.execute(() -> {
                platformOk.set(DUUIWorker.current().currentScope().isPresent());
                done.countDown();
            });
            virtual.execute(() -> {
                virtualOk.set(DUUIWorker.current().currentScope().isPresent());
                done.countDown();
            });
            assertTrue(done.await(5, TimeUnit.SECONDS));
        }

        assertTrue(platformOk.get());
        assertTrue(virtualOk.get());
    }
}
