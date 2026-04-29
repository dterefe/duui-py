package duui.runtime;

import duui.monitoring.model.DUUIScope;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

public final class DUUIWorker {
    private static final ConcurrentHashMap<Long, DUUIWorker> CURRENT = new ConcurrentHashMap<>();

    private final DUUIComposer composer;
    private final Thread ownerThread;
    private final Deque<DUUIScope> scopes = new ArrayDeque<>();

    DUUIWorker(DUUIComposer composer, Thread ownerThread) {
        this.composer = Objects.requireNonNull(composer, "composer");
        this.ownerThread = Objects.requireNonNull(ownerThread, "ownerThread");
    }

    static DUUIWorker main(DUUIComposer composer, Thread thread) {
        DUUIWorker worker = new DUUIWorker(composer, thread);
        composer.runtime().register(thread, worker);
        return worker;
    }

    static void registerCurrentThread(DUUIWorker worker) {
        CURRENT.put(Thread.currentThread().threadId(), worker);
    }

    static void clearCurrentThread(Thread thread) {
        CURRENT.remove(thread.threadId());
    }

    public static DUUIWorker current() {
        DUUIWorker worker = CURRENT.get(Thread.currentThread().threadId());
        if (worker == null) {
            throw new IllegalStateException("Current thread is not registered as a DUUI worker");
        }
        return worker;
    }

    public static Optional<DUUIWorker> currentOptional() {
        return Optional.ofNullable(CURRENT.get(Thread.currentThread().threadId()));
    }

    public DUUIComposer composer() {
        return composer;
    }

    public DUUIRuntime runtime() {
        return composer.runtime();
    }

    public Thread ownerThread() {
        return ownerThread;
    }

    public synchronized void pushScope(DUUIScope scope) {
        scopes.push(Objects.requireNonNull(scope, "scope"));
    }

    public synchronized void popScope() {
        if (!scopes.isEmpty()) {
            scopes.pop();
        }
    }

    public synchronized Optional<DUUIScope> currentScope() {
        return Optional.ofNullable(scopes.peek());
    }

    public synchronized List<DUUIScope> snapshotScopes() {
        return List.copyOf(scopes);
    }

    synchronized void restoreScopes(List<DUUIScope> snapshot) {
        scopes.clear();
        for (int i = snapshot.size() - 1; i >= 0; i--) {
            scopes.push(snapshot.get(i));
        }
    }

    public Runnable wrap(Runnable delegate) {
        Objects.requireNonNull(delegate, "delegate");
        List<DUUIScope> snapshot = snapshotScopes();
        return () -> {
            Thread currentThread = Thread.currentThread();
            DUUIWorker taskWorker = new DUUIWorker(composer, currentThread);
            runtime().register(currentThread, taskWorker);
            taskWorker.restoreScopes(snapshot);
            try {
                delegate.run();
            } finally {
                runtime().unregister(currentThread);
            }
        };
    }

    public DUUIPlatformExecutor platformExecutor(int parallelism, String threadPrefix) {
        return new DUUIPlatformExecutor(
            this,
            parallelism,
            parallelism,
            30L,
            TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(),
            Thread.ofPlatform().name(threadPrefix + "-", 0).factory()
        );
    }

    public DUUIVirtualExecutor virtualExecutor(String threadPrefix) {
        return new DUUIVirtualExecutor(this, threadPrefix);
    }
}
