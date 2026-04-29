package duui.monitoring.model;

import java.util.Map;
import java.util.Objects;

public record DUUIScope(
    String id,
    String name,
    String parentId,
    Map<String, String> context
) {
    public DUUIScope {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(name, "name");
        context = context == null ? Map.of() : Map.copyOf(context);
    }
}
