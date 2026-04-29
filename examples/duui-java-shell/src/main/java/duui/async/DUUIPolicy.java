package duui.async;

import java.util.List;

public record DUUIPolicy(
        DUUIResolvedConfiguration configuration,
        DUUIMetadata metadata,
        DUUIExecutionPlan execution,
        List<DUUIWrapperAction> actions
) {
    public DUUIPolicy {
        actions = List.copyOf(actions == null ? List.of() : actions);
    }
}
