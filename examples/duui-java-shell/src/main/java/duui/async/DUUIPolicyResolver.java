package duui.async;

import java.util.ArrayList;
import java.util.List;

public final class DUUIPolicyResolver {
    private final DUUIConfiguration configuration;

    public DUUIPolicyResolver(DUUIConfiguration configuration) {
        this.configuration = configuration;
    }

    public DUUIPolicy resolve(DUUIInvocation invocation) {
        DUUIResolvedConfiguration resolved = configuration.resolve(invocation);
        List<DUUIWrapperAction> actions = new ArrayList<>(resolved.actions());
        if (!resolved.trackers().isEmpty()) {
            actions.add(new DUUITrackerAction(resolved.trackers()));
        }
        return new DUUIPolicy(resolved, resolved.metadata(), resolved.execution(), actions);
    }
}
