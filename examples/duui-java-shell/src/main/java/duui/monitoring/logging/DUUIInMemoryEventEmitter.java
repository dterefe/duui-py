package duui.monitoring.logging;

import duui.monitoring.model.DUUIMonitoringEvent;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

public final class DUUIInMemoryEventEmitter implements DUUIEventEmitter {
    private final CopyOnWriteArrayList<DUUIMonitoringEvent> events = new CopyOnWriteArrayList<>();

    @Override
    public void emit(DUUIMonitoringEvent event) {
        events.add(event);
    }

    public List<DUUIMonitoringEvent> events() {
        return List.copyOf(events);
    }
}
