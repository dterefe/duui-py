package duui.async;

import java.time.Instant;
import java.util.Objects;

public record DUUIOshiCpuSample(Instant at, double systemCpuLoad) {
    public DUUIOshiCpuSample {
        Objects.requireNonNull(at, "at");
    }
}
