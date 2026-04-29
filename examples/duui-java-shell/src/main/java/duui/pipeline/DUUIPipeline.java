package duui.pipeline;

import duui.runtime.DUUIComposer;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public final class DUUIPipeline {
    private final List<DUUICheckpoint> checkpoints = new ArrayList<>();
    private DUUIComposer composer;

    public DUUIPipeline add(DUUICheckpoint checkpoint) {
        checkpoints.add(Objects.requireNonNull(checkpoint, "checkpoint"));
        return this;
    }

    public List<DUUICheckpoint> checkpoints() {
        return List.copyOf(checkpoints);
    }

    public List<DUUIProcessorCheckpoint> processorCheckpoints() {
        return checkpoints.stream()
            .filter(DUUIProcessorCheckpoint.class::isInstance)
            .map(DUUIProcessorCheckpoint.class::cast)
            .toList();
    }

    public DUUISourceCheckpoint sourceCheckpoint() {
        return checkpoints.stream()
            .filter(DUUISourceCheckpoint.class::isInstance)
            .map(DUUISourceCheckpoint.class::cast)
            .findFirst()
            .orElseThrow(() -> new IllegalStateException("Pipeline has no source checkpoint"));
    }

    public DUUITargetCheckpoint targetCheckpoint() {
        return checkpoints.stream()
            .filter(DUUITargetCheckpoint.class::isInstance)
            .map(DUUITargetCheckpoint.class::cast)
            .findFirst()
            .orElseThrow(() -> new IllegalStateException("Pipeline has no target checkpoint"));
    }

    public void attach(DUUIComposer composer) {
        this.composer = Objects.requireNonNull(composer, "composer");
    }

    public DUUIComposer composer() {
        return composer;
    }
}
