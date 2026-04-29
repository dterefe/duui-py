package duui.async;

import java.lang.reflect.Method;
import java.util.Objects;
import java.util.Set;

public record DUUIInvocation(
        Class<?> ownerType,
        Method method,
        Async annotation,
        DUUIWorker worker,
        Set<DUUIEntity> entities
) {
    public DUUIInvocation {
        Objects.requireNonNull(ownerType, "ownerType");
        Objects.requireNonNull(method, "method");
        Objects.requireNonNull(annotation, "annotation");
        Objects.requireNonNull(worker, "worker");
        entities = Set.copyOf(Objects.requireNonNull(entities, "entities"));
    }
}
