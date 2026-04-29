package duui.async;

import java.util.Objects;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicLong;

public final class DUUIFactory implements ThreadFactory {
    private final DUUIRuntime runtime;
    private final DUUIWorkerKind kind;
    private final String namePrefix;
    private final DUUIUlids ulids = new DUUIUlids();
    private final AtomicLong counter = new AtomicLong();

    public DUUIFactory(DUUIRuntime runtime, DUUIWorkerKind kind, String namePrefix) {
        this.runtime = Objects.requireNonNull(runtime, "runtime");
        this.kind = Objects.requireNonNull(kind, "kind");
        this.namePrefix = Objects.requireNonNull(namePrefix, "namePrefix");
    }

    @Override
    public DUUIWorker newThread(Runnable task) {
        String name = namePrefix + "-" + kind.name().toLowerCase() + "-" + counter.getAndIncrement();
        return new DUUIWorker(new DUUIId("worker", name, ulids.next()), runtime, task);
    }
}
