package duui.async;

import java.util.List;
import java.util.Objects;

public record DUUIResolvedConfiguration(
        DUUIMetadata metadata,
        DUUIExecutionPlan execution,
        List<DUUIWrapperAction> actions,
        List<DUUITrackerFactory> trackers
) {
    public DUUIResolvedConfiguration(DUUIMetadata metadata, DUUIExecutionPlan execution, List<DUUIWrapperAction> actions) {
        this(metadata, execution, actions, List.of());
    }

    public DUUIResolvedConfiguration {
        metadata = metadata == null ? new DUUIMetadata() : metadata;
        execution = execution == null ? DUUIExecutionPlan.defaults() : execution;
        actions = List.copyOf(Objects.requireNonNullElse(actions, List.of()));
        trackers = List.copyOf(Objects.requireNonNullElse(trackers, List.of()));
    }

    public static DUUIResolvedConfiguration defaults() {
        return new DUUIResolvedConfiguration(new DUUIMetadata(), DUUIExecutionPlan.defaults(), List.of(), List.of());
    }
}
