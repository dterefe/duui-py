package duui.async;

public final class DUUIRuntime {
    private final DUUIRegistry registry = new DUUIRegistry();
    private final DUUIConfiguration configuration = new DUUIConfiguration();
    private final DUUIPolicyResolver policies = new DUUIPolicyResolver(configuration);
    private final DUUIExecutors executors = new DUUIExecutors(this);
    private final DUUIDispatcher dispatcher = new DUUIDispatcher(executors);
    private final DUUIPhaseFactory phases = new DUUIPhaseFactory();
    private final DUUIWrapperKernel wrapper = new DUUIWrapperKernel();
    private final DUUIErrorHandler errors = new DUUIErrorHandler();

    public DUUIRegistry registry() {
        return registry;
    }

    public DUUIConfiguration configuration() {
        return configuration;
    }

    public DUUIPolicyResolver policies() {
        return policies;
    }

    public DUUIExecutors executors() {
        return executors;
    }

    public DUUIDispatcher dispatcher() {
        return dispatcher;
    }

    public DUUIPhaseFactory phases() {
        return phases;
    }

    public DUUIWrapperKernel wrapper() {
        return wrapper;
    }

    public DUUIErrorHandler errors() {
        return errors;
    }

    public void close() {
        executors.close();
    }
}
