package duui.runtime;

import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

public final class DUUIRuntime {
    private final DUUIComposer composer;
    private final ConcurrentHashMap<Class<?>, Object> services = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<Long, DUUIWorker> workers = new ConcurrentHashMap<>();

    DUUIRuntime(DUUIComposer composer) {
        this.composer = Objects.requireNonNull(composer, "composer");
    }

    public DUUIComposer composer() {
        return composer;
    }

    public <T> void installService(Class<T> type, T service) {
        services.put(Objects.requireNonNull(type, "type"), Objects.requireNonNull(service, "service"));
    }

    public <T> T service(Class<T> type) {
        Object service = services.get(Objects.requireNonNull(type, "type"));
        if (service == null) {
            throw new IllegalStateException("No service registered for " + type.getName());
        }
        return type.cast(service);
    }

    public <T> Optional<T> serviceOptional(Class<T> type) {
        return Optional.ofNullable(type.cast(services.get(type)));
    }

    DUUIWorker register(Thread thread, DUUIWorker worker) {
        workers.put(thread.threadId(), worker);
        DUUIWorker.registerCurrentThread(worker);
        return worker;
    }

    void unregister(Thread thread) {
        workers.remove(thread.threadId());
        DUUIWorker.clearCurrentThread(thread);
    }

    public Optional<DUUIWorker> worker(Thread thread) {
        return Optional.ofNullable(workers.get(thread.threadId()));
    }

    public Map<Long, DUUIWorker> workers() {
        return Map.copyOf(workers);
    }
}
