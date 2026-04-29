package duui.pipeline;

import duui.ems.DUUIActor;

import java.util.List;

public abstract class DUUIStage extends DUUIActor {
    private final List<DUUIComponent> components;

    protected DUUIStage(String id, List<DUUIComponent> components) {
        super(id);
        this.components = List.copyOf(components);
    }

    public List<DUUIComponent> components() {
        return components;
    }

    public abstract DispatchShape shape();

    public enum DispatchShape {
        MONO,
        PARALLEL,
        LINEAR
    }
}
