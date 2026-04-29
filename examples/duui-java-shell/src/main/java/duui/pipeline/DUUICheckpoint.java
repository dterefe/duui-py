package duui.pipeline;

import duui.ems.DUUIActor;
import duui.ems.DUUIArtifact;

import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

public abstract class DUUICheckpoint extends DUUIActor {
    private final BlockingQueue<DUUIArtifact<?>> queue = new LinkedBlockingQueue<>();
    private final DUUIStage stage;

    protected DUUICheckpoint(String id, DUUIStage stage) {
        super(id);
        this.stage = stage;
    }

    public Optional<DUUIArtifact<?>> poll() {
        return Optional.ofNullable(queue.poll());
    }

    public void offer(DUUIArtifact<?> artifact) {
        queue.offer(Objects.requireNonNull(artifact, "artifact"));
    }

    public int size() {
        return queue.size();
    }

    public DUUIStage stage() {
        return stage;
    }
}
