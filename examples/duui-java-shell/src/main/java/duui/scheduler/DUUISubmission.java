package duui.scheduler;

import duui.ems.DUUIArtifact;
import duui.pipeline.DUUICheckpoint;
import duui.pipeline.DUUINode;
import duui.pipeline.DUUIStage;

import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicReference;

public final class DUUISubmission {
    public enum State {
        SUBMITTED,
        RUNNING,
        COMPLETED,
        FAILED,
        CANCELLED
    }

    private final String id;
    private final DUUICheckpoint checkpoint;
    private final DUUIStage stage;
    private final DUUINode node;
    private final DUUIArtifact<?> artifact;
    private final CompletableFuture<?> completionFuture;
    private final Runnable cancellation;
    private final AtomicReference<State> state = new AtomicReference<>(State.SUBMITTED);

    public DUUISubmission(
        String id,
        DUUICheckpoint checkpoint,
        DUUIStage stage,
        DUUINode node,
        DUUIArtifact<?> artifact,
        CompletableFuture<?> completionFuture,
        Runnable cancellation
    ) {
        this.id = Objects.requireNonNull(id, "id");
        this.checkpoint = checkpoint;
        this.stage = stage;
        this.node = node;
        this.artifact = artifact;
        this.completionFuture = Objects.requireNonNull(completionFuture, "completionFuture");
        this.cancellation = Objects.requireNonNull(cancellation, "cancellation");
    }

    public String id() {
        return id;
    }

    public DUUICheckpoint checkpoint() {
        return checkpoint;
    }

    public DUUIStage stage() {
        return stage;
    }

    public DUUINode node() {
        return node;
    }

    public DUUIArtifact<?> artifact() {
        return artifact;
    }

    public CompletableFuture<?> completionFuture() {
        return completionFuture;
    }

    public void cancel() {
        state.set(State.CANCELLED);
        cancellation.run();
    }

    public State state() {
        return state.get();
    }

    public void state(State value) {
        state.set(value);
    }
}
