package duui.monitoring.logging;

import duui.monitoring.model.DUUIMonitoringEvent;

import java.util.List;
import java.util.Objects;
import java.util.concurrent.CopyOnWriteArrayList;

public final class DUUICompositeEventEmitter implements DUUIEventEmitter {
    private final CopyOnWriteArrayList<DUUIEventEmitter> emitters = new CopyOnWriteArrayList<>();

    public DUUICompositeEventEmitter(List<DUUIEventEmitter> emitters) {
        if (emitters != null) {
            this.emitters.addAll(emitters);
        }
    }

    public void register(DUUIEventEmitter emitter) {
        emitters.add(Objects.requireNonNull(emitter, "emitter"));
    }

    public void unregister(DUUIEventEmitter emitter) {
        emitters.remove(emitter);
    }

    @Override
    public void emit(DUUIMonitoringEvent event) {
        for (DUUIEventEmitter emitter : emitters) {
            emitter.emit(event);
        }
    }
}
