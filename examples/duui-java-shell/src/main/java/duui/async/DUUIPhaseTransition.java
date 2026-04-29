package duui.async;

import java.time.Instant;
import java.util.Objects;

public record DUUIPhaseTransition(DUUILifecycle lifecycle, Instant at) {
    public DUUIPhaseTransition {
        Objects.requireNonNull(lifecycle, "lifecycle");
        Objects.requireNonNull(at, "at");
    }
}
