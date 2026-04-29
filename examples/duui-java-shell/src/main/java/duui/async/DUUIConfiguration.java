package duui.async;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

public final class DUUIConfiguration {
    private volatile DUUIResolvedConfiguration root = DUUIResolvedConfiguration.defaults();
    private final Map<String, DUUIResolvedConfiguration> byPhaseName = new ConcurrentHashMap<>();
    private final Map<Class<?>, DUUIResolvedConfiguration> byOwnerType = new ConcurrentHashMap<>();
    private final Map<Method, DUUIResolvedConfiguration> byMethod = new ConcurrentHashMap<>();
    private final Map<DUUIId, DUUIResolvedConfiguration> byEntity = new ConcurrentHashMap<>();
    private final List<DUUIExtension> extensions = new CopyOnWriteArrayList<>();

    public DUUIResolvedConfiguration resolve(DUUIInvocation invocation) {
        DUUIResolvedConfiguration resolved = root;
        resolved = merge(resolved, byOwnerType.get(invocation.ownerType()));
        resolved = merge(resolved, byPhaseName.get(invocation.annotation().name()));
        resolved = merge(resolved, byMethod.get(invocation.method()));
        for (DUUIEntity entity : invocation.entities()) {
            resolved = merge(resolved, byEntity.get(entity.duuiId()));
        }

        List<DUUIWrapperAction> actions = new ArrayList<>(resolved.actions());
        for (DUUIExtension extension : extensions) {
            actions.addAll(extension.actions(invocation, resolved));
        }
        return new DUUIResolvedConfiguration(resolved.metadata(), resolved.execution(), actions, resolved.trackers());
    }

    public void apply(DUUIConfigurationPatch patch) {
        if (patch.root() != null) {
            root = patch.root();
        }
        byPhaseName.putAll(patch.byPhaseName());
        byOwnerType.putAll(patch.byOwnerType());
        byMethod.putAll(patch.byMethod());
        byEntity.putAll(patch.byEntity());
        extensions.addAll(patch.extensions());
    }

    private DUUIResolvedConfiguration merge(DUUIResolvedConfiguration base, DUUIResolvedConfiguration override) {
        if (override == null) {
            return base;
        }
        List<DUUIWrapperAction> actions = new ArrayList<>(base.actions());
        actions.addAll(override.actions());
        List<DUUITrackerFactory> trackers = new ArrayList<>(base.trackers());
        trackers.addAll(override.trackers());
        return new DUUIResolvedConfiguration(
                base.metadata().merge(override.metadata()),
                base.execution().merge(new DUUIExecutionPlanPatch(
                        override.execution().mode(),
                        override.execution().scopeMode(),
                        override.execution().outsideScopeBehavior(),
                        override.execution().timeout()
                )),
                actions,
                trackers
        );
    }
}
