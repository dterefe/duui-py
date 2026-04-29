package duui.async;

import java.util.Objects;

public record DUUIId(String type, String name, String ulid) {
    public DUUIId {
        Objects.requireNonNull(type, "type");
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(ulid, "ulid");
    }
}
