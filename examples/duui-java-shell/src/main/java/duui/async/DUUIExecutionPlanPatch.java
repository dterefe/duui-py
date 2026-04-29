package duui.async;

import java.time.Duration;

public record DUUIExecutionPlanPatch(
        DUUIExecutionMode mode,
        DUUIScopeMode scopeMode,
        DUUIOutsideScopeBehavior outsideScopeBehavior,
        Duration timeout
) {
}
