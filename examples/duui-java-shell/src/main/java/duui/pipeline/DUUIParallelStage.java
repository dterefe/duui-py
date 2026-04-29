package duui.pipeline;

import java.util.List;

public final class DUUIParallelStage extends DUUIStage {
    public DUUIParallelStage(String id, List<DUUIComponent> components) {
        super(id, components);
    }

    @Override
    public DispatchShape shape() {
        return DispatchShape.PARALLEL;
    }
}
