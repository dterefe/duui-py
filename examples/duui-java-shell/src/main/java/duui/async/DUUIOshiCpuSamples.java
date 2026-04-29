package duui.async;

import java.util.ArrayList;
import java.util.List;

public final class DUUIOshiCpuSamples {
    private final List<DUUIOshiCpuSample> samples = new ArrayList<>();

    public synchronized void add(DUUIOshiCpuSample sample) {
        samples.add(sample);
    }

    public synchronized List<DUUIOshiCpuSample> samples() {
        return List.copyOf(samples);
    }

    public synchronized int size() {
        return samples.size();
    }
}
