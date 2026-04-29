package duui.async;

import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;

public class DUUIWorker extends Thread implements DUUIEntity {
    private static final Map<Thread, DUUIWorker> CURRENT = new ConcurrentHashMap<>();

    private final DUUIId id;
    private final DUUIRuntime runtime;
    private final DUUIContext context;
    private final Runnable task;
    private final boolean externalThreadBinding;

    public DUUIWorker(DUUIId id, DUUIRuntime runtime, Runnable task) {
        super(Objects.requireNonNull(task, "task"), id.name());
        this.id = Objects.requireNonNull(id, "id");
        this.runtime = Objects.requireNonNull(runtime, "runtime");
        this.context = new DUUIContext(this);
        this.task = task;
        this.externalThreadBinding = false;
    }

    private DUUIWorker(DUUIId id, DUUIRuntime runtime, Thread boundThread) {
        super(id.name());
        this.id = Objects.requireNonNull(id, "id");
        this.runtime = Objects.requireNonNull(runtime, "runtime");
        this.context = new DUUIContext(this);
        this.task = null;
        this.externalThreadBinding = true;
        CURRENT.put(Objects.requireNonNull(boundThread, "boundThread"), this);
    }

    static DUUIWorker bindCurrent(DUUIId id, DUUIRuntime runtime) {
        return new DUUIWorker(id, runtime, Thread.currentThread());
    }

    static void unbindCurrent() {
        CURRENT.remove(Thread.currentThread());
    }

    @Override
    public final void run() {
        if (externalThreadBinding) {
            throw new DUUIRuntimeException("bound DUUI main worker cannot be started");
        }
        CURRENT.put(Thread.currentThread(), this);
        runtime.registry().registerWorker(this);
        try {
            task.run();
        } finally {
            runtime.registry().unregisterWorker(this);
            CURRENT.remove(Thread.currentThread());
        }
    }

    @Override
    public DUUIId duuiId() {
        return id;
    }

    public DUUIRuntime runtime() {
        return runtime;
    }

    public DUUIContext context() {
        return context;
    }

    public static DUUIWorker current() {
        return CURRENT.get(Thread.currentThread());
    }

    public static DUUIWorker requireCurrent() {
        DUUIWorker worker = current();
        if (worker == null) {
            throw new DUUIRuntimeException("current thread is not a DUUI worker");
        }
        return worker;
    }
}
