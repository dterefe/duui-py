package duui.runtime;

import java.util.List;
import java.util.Objects;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

public class DUUIPlatformExecutor extends ThreadPoolExecutor {
    private final DUUIWorker owner;

    public DUUIPlatformExecutor(
        DUUIWorker owner,
        int corePoolSize,
        int maximumPoolSize,
        long keepAliveTime,
        TimeUnit unit,
        BlockingQueue<Runnable> workQueue,
        ThreadFactory threadFactory
    ) {
        super(corePoolSize, maximumPoolSize, keepAliveTime, unit, workQueue, threadFactory);
        this.owner = Objects.requireNonNull(owner, "owner");
    }

    @Override
    public void execute(Runnable command) {
        super.execute(new WorkerBoundRunnable(owner, command, owner.snapshotScopes()));
    }

    @Override
    protected void beforeExecute(Thread thread, Runnable runnable) {
        super.beforeExecute(thread, runnable);
        if (runnable instanceof WorkerBoundRunnable bound) {
            DUUIWorker worker = new DUUIWorker(owner.composer(), thread);
            owner.runtime().register(thread, worker);
            worker.restoreScopes(bound.scopeSnapshot());
        }
    }

    @Override
    protected void afterExecute(Runnable runnable, Throwable throwable) {
        try {
            owner.runtime().unregister(Thread.currentThread());
        } finally {
            super.afterExecute(runnable, throwable);
        }
    }

    record WorkerBoundRunnable(DUUIWorker owner, Runnable delegate, List<duui.monitoring.model.DUUIScope> scopeSnapshot)
        implements Runnable {
        @Override
        public void run() {
            delegate.run();
        }
    }
}
