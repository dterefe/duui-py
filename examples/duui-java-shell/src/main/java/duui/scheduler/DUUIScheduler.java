package duui.scheduler;

import duui.ems.DUUIArtifact;
import duui.pipeline.DUUICheckpoint;
import duui.pipeline.DUUIPipeline;
import duui.pipeline.DUUIProcessorCheckpoint;
import duui.pipeline.DUUISourceCheckpoint;
import duui.pipeline.DUUITargetCheckpoint;

import java.util.List;
import java.util.Objects;

public final class DUUIScheduler {
    private final DUUIPipeline pipeline;
    private boolean sourceDrained;

    public DUUIScheduler(DUUIPipeline pipeline) {
        this.pipeline = Objects.requireNonNull(pipeline, "pipeline");
    }

    public void markSourceDrained() {
        sourceDrained = true;
    }

    public Step next() {
        DUUISourceCheckpoint source = pipeline.sourceCheckpoint();
        if (source.size() > 0) {
            DUUIArtifact<?> artifact = source.poll().orElseThrow();
            DUUIProcessorCheckpoint firstProcessor = pipeline.processorCheckpoints().stream().findFirst().orElse(null);
            if (firstProcessor == null) {
                pipeline.targetCheckpoint().offer(artifact);
                return new TargetCheckpointStep(pipeline.targetCheckpoint(), artifact);
            }
            return new SourceCheckpointStep(source, firstProcessor, artifact);
        }

        List<DUUIProcessorCheckpoint> processors = pipeline.processorCheckpoints();
        for (int i = 0; i < processors.size(); i++) {
            DUUIProcessorCheckpoint checkpoint = processors.get(i);
            if (checkpoint.size() == 0) {
                continue;
            }
            DUUIArtifact<?> artifact = checkpoint.poll().orElseThrow();
            DUUICheckpoint next = i + 1 < processors.size() ? processors.get(i + 1) : pipeline.targetCheckpoint();
            return new ProcessorCheckpointStep(checkpoint, next, artifact);
        }

        DUUITargetCheckpoint target = pipeline.targetCheckpoint();
        if (target.size() > 0) {
            return new TargetCheckpointStep(target, target.poll().orElseThrow());
        }

        if (sourceDrained) {
            return CompleteStep.INSTANCE;
        }
        return IdleStep.INSTANCE;
    }

    public sealed interface Step permits SourceCheckpointStep, ProcessorCheckpointStep, TargetCheckpointStep, IdleStep, CompleteStep {
    }

    public record SourceCheckpointStep(DUUISourceCheckpoint source, DUUIProcessorCheckpoint target, DUUIArtifact<?> artifact)
        implements Step {
    }

    public record ProcessorCheckpointStep(DUUIProcessorCheckpoint source, DUUICheckpoint target, DUUIArtifact<?> artifact)
        implements Step {
    }

    public record TargetCheckpointStep(DUUITargetCheckpoint checkpoint, DUUIArtifact<?> artifact) implements Step {
    }

    public enum IdleStep implements Step {
        INSTANCE
    }

    public enum CompleteStep implements Step {
        INSTANCE
    }
}
