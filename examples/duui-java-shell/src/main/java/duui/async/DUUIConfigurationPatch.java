package duui.async;

import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;

public record DUUIConfigurationPatch(
        DUUIResolvedConfiguration root,
        Map<String, DUUIResolvedConfiguration> byPhaseName,
        Map<Class<?>, DUUIResolvedConfiguration> byOwnerType,
        Map<Method, DUUIResolvedConfiguration> byMethod,
        Map<DUUIId, DUUIResolvedConfiguration> byEntity,
        List<DUUIExtension> extensions
) {
    public DUUIConfigurationPatch {
        byPhaseName = byPhaseName == null ? Map.of() : Map.copyOf(byPhaseName);
        byOwnerType = byOwnerType == null ? Map.of() : Map.copyOf(byOwnerType);
        byMethod = byMethod == null ? Map.of() : Map.copyOf(byMethod);
        byEntity = byEntity == null ? Map.of() : Map.copyOf(byEntity);
        extensions = extensions == null ? List.of() : List.copyOf(extensions);
    }
}
