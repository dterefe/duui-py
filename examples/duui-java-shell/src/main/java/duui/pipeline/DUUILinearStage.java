package duui.pipeline;

import java.util.List;

public final class DUUILinearStage extends DUUIStage {
    public DUUILinearStage(String id, List<DUUIComponent> components) {
        super(id, components);
    }

    @Override
    public DispatchShape shape() {
        return DispatchShape.LINEAR;
    }
}
