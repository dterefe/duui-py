package duui.monitoring.logging;

import duui.monitoring.model.DUUIMonitoringEvent;

@FunctionalInterface
public interface DUUIEventEmitter {
    void emit(DUUIMonitoringEvent event);
}
