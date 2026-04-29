package duui.async;

import jdk.jfr.Event;
import jdk.jfr.Label;
import jdk.jfr.Name;

public final class DUUIJfrPhaseTracker implements DUUITracker {
    private DUUIPhase phase;

    @Override
    public void init(DUUIPhase phase) {
        this.phase = phase;
        DUUIJfrPhaseEvent event = new DUUIJfrPhaseEvent();
        event.phase = phase.duuiId().name();
        event.lifecycle = "init";
        event.commit();
    }

    @Override
    public void start() {
        DUUIJfrPhaseEvent event = new DUUIJfrPhaseEvent();
        event.phase = phase.duuiId().name();
        event.lifecycle = "start";
        event.commit();
        phase.trackerState().jfr().started();
    }

    @Override
    public void stop() {
        DUUIJfrPhaseEvent event = new DUUIJfrPhaseEvent();
        event.phase = phase.duuiId().name();
        event.lifecycle = "stop";
        event.commit();
        phase.trackerState().jfr().stopped();
    }

    @Name("duui.Phase")
    @Label("DUUI Phase")
    static final class DUUIJfrPhaseEvent extends Event {
        @Label("Phase")
        String phase;

        @Label("Lifecycle")
        String lifecycle;
    }
}
