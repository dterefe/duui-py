package duui.async;

import oshi.SystemInfo;
import oshi.hardware.CentralProcessor;

import java.time.Duration;
import java.time.Instant;

public final class DUUIOshiCpuRecorder extends DUUIIntervalRecorder {
    private final CentralProcessor processor = new SystemInfo().getHardware().getProcessor();
    private long[] previousTicks = processor.getSystemCpuLoadTicks();

    public DUUIOshiCpuRecorder(Duration interval) {
        super(interval);
    }

    @Override
    protected void record(DUUIPhase phase) {
        double load = processor.getSystemCpuLoadBetweenTicks(previousTicks);
        previousTicks = processor.getSystemCpuLoadTicks();
        phase.trackerState().oshiCpu().add(new DUUIOshiCpuSample(Instant.now(), load));
    }
}
