package duui.async;

import java.util.LinkedHashSet;
import java.util.Set;

public final class DUUIMetadata {
    private final Set<String> traits = new LinkedHashSet<>();

    public DUUIMetadata() {
    }

    public DUUIMetadata(Set<String> traits) {
        if (traits != null) {
            this.traits.addAll(traits);
        }
    }

    public Set<String> traits() {
        return Set.copyOf(traits);
    }

    public boolean hasTrait(String trait) {
        return traits.contains(trait);
    }

    public DUUIMetadata merge(DUUIMetadata other) {
        LinkedHashSet<String> merged = new LinkedHashSet<>(traits);
        if (other != null) {
            merged.addAll(other.traits);
        }
        return new DUUIMetadata(merged);
    }
}
