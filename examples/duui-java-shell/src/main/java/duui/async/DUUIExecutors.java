package duui.async;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class DUUIExecutors implements AutoCloseable {
    private final ExecutorService direct = new DirectExecutorService();
    private final ExecutorService platform;
    private final ExecutorService virtual;

    public DUUIExecutors(DUUIRuntime runtime) {
        DUUIFactory platformFactory = new DUUIFactory(runtime, DUUIWorkerKind.PLATFORM, "duui");
        DUUIFactory virtualFactory = new DUUIFactory(runtime, DUUIWorkerKind.VIRTUAL, "duui");
        this.platform = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors(), platformFactory);
        this.virtual = Executors.newThreadPerTaskExecutor(virtualFactory);
    }

    public ExecutorService executor(DUUIExecutionMode mode) {
        return switch (mode) {
            case DIRECT -> direct;
            case PLATFORM -> platform;
            case VIRTUAL -> virtual;
        };
    }

    public ExecutorService platform() {
        return platform;
    }

    public ExecutorService virtual() {
        return virtual;
    }

    public ExecutorService direct() {
        return direct;
    }

    @Override
    public void close() {
        direct.shutdown();
        platform.close();
        virtual.close();
    }
}
