package duui.scheduler;

import duui.pipeline.DUUICheckpoint;
import duui.pipeline.DUUIComponent;
import duui.pipeline.DUUIStage;

import java.util.List;

public record DUUISchedulerPolicy(
    SourcePollingPolicy sourcePollingPolicy,
    CheckpointSelectionPolicy checkpointSelectionPolicy,
    StageDispatchPolicy stageDispatchPolicy,
    RetryFailurePolicy retryFailurePolicy
) {
    public DUUISchedulerPolicy {
        sourcePollingPolicy = sourcePollingPolicy == null ? step -> true : sourcePollingPolicy;
        checkpointSelectionPolicy = checkpointSelectionPolicy == null ? checkpoints -> checkpoints.stream().findFirst().orElse(null) : checkpointSelectionPolicy;
        stageDispatchPolicy = stageDispatchPolicy == null ? DUUIStage::components : stageDispatchPolicy;
        retryFailurePolicy = retryFailurePolicy == null ? (submission, failure) -> false : retryFailurePolicy;
    }

    @FunctionalInterface
    public interface SourcePollingPolicy {
        boolean shouldPoll(DUUIScheduler.Step step);
    }

    @FunctionalInterface
    public interface CheckpointSelectionPolicy {
        DUUICheckpoint select(List<DUUICheckpoint> checkpoints);
    }

    @FunctionalInterface
    public interface StageDispatchPolicy {
        List<DUUIComponent> select(DUUIStage stage);
    }

    @FunctionalInterface
    public interface RetryFailurePolicy {
        boolean shouldRetry(DUUISubmission submission, Throwable failure);
    }

    public static DUUISchedulerPolicy standard() {
        return new DUUISchedulerPolicy(null, null, null, null);
    }
}
