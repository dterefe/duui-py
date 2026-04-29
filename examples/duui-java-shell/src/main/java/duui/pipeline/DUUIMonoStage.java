package duui.pipeline;

import java.util.List;

public final class DUUIMonoStage extends DUUIStage {
    public DUUIMonoStage(String id, DUUIComponent component) {
        super(id, List.of(component));
    }

    @Override
    public DispatchShape shape() {
        return DispatchShape.MONO;
    }
}
