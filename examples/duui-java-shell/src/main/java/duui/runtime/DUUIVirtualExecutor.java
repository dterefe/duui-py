package duui.runtime;

import java.util.List;
import java.util.Objects;
import java.util.concurrent.AbstractExecutorService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public final class DUUIVirtualExecutor extends AbstractExecutorService {
    private final DUUIWorker owner;
    private final ExecutorService delegate;

    public DUUIVirtualExecutor(DUUIWorker owner, String threadPrefix) {
        this.owner = Objects.requireNonNull(owner, "owner");
        this.delegate = Executors.newThreadPerTaskExecutor(Thread.ofVirtual().name(threadPrefix + "-", 0).factory());
    }

    @Override
    public void shutdown() {
        delegate.shutdown();
    }

    @Override
    public List<Runnable> shutdownNow() {
        return delegate.shutdownNow();
    }

    @Override
    public boolean isShutdown() {
        return delegate.isShutdown();
    }

    @Override
    public boolean isTerminated() {
        return delegate.isTerminated();
    }

    @Override
    public boolean awaitTermination(long timeout, TimeUnit unit) throws InterruptedException {
        return delegate.awaitTermination(timeout, unit);
    }

    @Override
    public void execute(Runnable command) {
        delegate.execute(owner.wrap(command));
    }
}
