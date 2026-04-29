package duui.async;

import java.time.Duration;

public record DUUIExecutionPlan(
        DUUIExecutionMode mode,
        DUUIScopeMode scopeMode,
        DUUIOutsideScopeBehavior outsideScopeBehavior,
        Duration timeout
) {
    public static DUUIExecutionPlan defaults() {
        return new DUUIExecutionPlan(
                DUUIExecutionMode.PLATFORM,
                DUUIScopeMode.SEQUENTIAL,
                DUUIOutsideScopeBehavior.THROW,
                null
        );
    }

    public DUUIExecutionPlan merge(DUUIExecutionPlanPatch patch) {
        if (patch == null) {
            return this;
        }
        return new DUUIExecutionPlan(
                patch.mode() == null ? mode : patch.mode(),
                patch.scopeMode() == null ? scopeMode : patch.scopeMode(),
                patch.outsideScopeBehavior() == null ? outsideScopeBehavior : patch.outsideScopeBehavior(),
                patch.timeout() == null ? timeout : patch.timeout()
        );
    }
}
