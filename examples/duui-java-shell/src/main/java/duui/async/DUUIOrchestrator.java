package duui.async;

public final class DUUIOrchestrator implements AutoCloseable {
    private final DUUIRuntime runtime;
    private final DUUIWorker mainWorker;

    public DUUIOrchestrator() {
        this.runtime = new DUUIRuntime();
        this.mainWorker = DUUIWorker.bindCurrent(new DUUIId("worker", "duui-main", new DUUIUlids().next()), runtime);
        runtime.registry().registerWorker(mainWorker);
    }

    public DUUIRuntime runtime() {
        return runtime;
    }

    public DUUIWorker mainWorker() {
        return mainWorker;
    }

    @Override
    public void close() {
        runtime.registry().unregisterWorker(mainWorker);
        DUUIWorker.unbindCurrent();
        runtime.close();
    }
}
