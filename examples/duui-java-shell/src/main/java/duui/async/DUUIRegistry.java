package duui.async;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public final class DUUIRegistry {
    private final Map<DUUIId, DUUIWorker> workers = new ConcurrentHashMap<>();
    private final Map<DUUIId, DUUIEntity> entities = new ConcurrentHashMap<>();
    private final Map<DUUIId, DUUIPhase> phases = new ConcurrentHashMap<>();
    private final Map<String, Set<DUUIWorker>> workersByName = new ConcurrentHashMap<>();
    private final Map<String, Set<DUUIEntity>> entitiesByName = new ConcurrentHashMap<>();
    private final Map<String, Set<DUUIEntity>> entitiesByType = new ConcurrentHashMap<>();
    private final Map<String, Set<DUUIPhase>> phasesByName = new ConcurrentHashMap<>();
    private final Map<DUUIId, Set<DUUIPhase>> phasesByEntity = new ConcurrentHashMap<>();

    public void registerWorker(DUUIWorker worker) {
        workers.put(worker.duuiId(), worker);
        add(workersByName, worker.duuiId().name(), worker);
        registerEntity(worker);
    }

    public void unregisterWorker(DUUIWorker worker) {
        workers.remove(worker.duuiId());
        remove(workersByName, worker.duuiId().name(), worker);
    }

    public void registerEntity(DUUIEntity entity) {
        entities.put(entity.duuiId(), entity);
        add(entitiesByName, entity.duuiId().name(), entity);
        add(entitiesByType, entity.duuiId().type(), entity);
    }

    public void registerPhase(DUUIPhase phase) {
        phases.put(phase.duuiId(), phase);
        add(phasesByName, phase.duuiId().name(), phase);
        registerEntity(phase);
        for (DUUIEntity entity : phase.entities()) {
            registerEntity(entity);
            add(phasesByEntity, entity.duuiId(), phase);
        }
    }

    public void unregisterPhase(DUUIPhase phase) {
        phases.remove(phase.duuiId());
        remove(phasesByName, phase.duuiId().name(), phase);
        remove(entitiesByName, phase.duuiId().name(), phase);
        remove(entitiesByType, phase.duuiId().type(), phase);
        for (DUUIEntity entity : phase.entities()) {
            remove(phasesByEntity, entity.duuiId(), phase);
        }
    }

    public Optional<DUUIWorker> worker(DUUIId id) {
        return Optional.ofNullable(workers.get(id));
    }

    public List<DUUIWorker> workers() {
        return List.copyOf(workers.values());
    }

    public List<DUUIWorker> workersNamed(String name) {
        return values(workersByName, name);
    }

    public Optional<DUUIEntity> entity(DUUIId id) {
        return Optional.ofNullable(entities.get(id));
    }

    public List<DUUIEntity> entities() {
        return List.copyOf(entities.values());
    }

    public List<DUUIEntity> entitiesNamed(String name) {
        return values(entitiesByName, name);
    }

    public List<DUUIEntity> entitiesOfType(String type) {
        return values(entitiesByType, type);
    }

    public Optional<DUUIPhase> phase(DUUIId id) {
        return Optional.ofNullable(phases.get(id));
    }

    public DUUIPhase requirePhase(DUUIId id) {
        return phase(id).orElseThrow(() -> new DUUIRuntimeException("unknown DUUI phase: " + id));
    }

    public DUUIPhase requirePhaseNamed(String name) {
        List<DUUIPhase> matches = phasesNamed(name);
        if (matches.isEmpty()) {
            throw new DUUIRuntimeException("unknown DUUI phase name: " + name);
        }
        if (matches.size() > 1) {
            throw new DUUIRuntimeException("ambiguous DUUI phase name: " + name);
        }
        return matches.getFirst();
    }

    public List<DUUIPhase> phases() {
        return List.copyOf(phases.values());
    }

    public List<DUUIPhase> phasesNamed(String name) {
        return values(phasesByName, name);
    }

    public List<DUUIPhase> phasesFor(DUUIEntity entity) {
        return values(phasesByEntity, entity.duuiId());
    }

    public List<DUUIPhase> rootPhases() {
        List<DUUIPhase> roots = new ArrayList<>();
        for (DUUIPhase phase : phases.values()) {
            if (phase.parent() == null) {
                roots.add(phase);
            }
        }
        return List.copyOf(roots);
    }

    private static <K, V> void add(Map<K, Set<V>> index, K key, V value) {
        index.computeIfAbsent(key, ignored -> Collections.synchronizedSet(new LinkedHashSet<>())).add(value);
    }

    private static <K, V> void remove(Map<K, Set<V>> index, K key, V value) {
        Set<V> values = index.get(key);
        if (values == null) {
            return;
        }
        values.remove(value);
        if (values.isEmpty()) {
            index.remove(key);
        }
    }

    private static <K, V> List<V> values(Map<K, Set<V>> index, K key) {
        Set<V> values = index.get(key);
        if (values == null) {
            return List.of();
        }
        synchronized (values) {
            return List.copyOf(values);
        }
    }
}
