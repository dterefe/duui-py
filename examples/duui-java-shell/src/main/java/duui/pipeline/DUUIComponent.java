package duui.pipeline;

import duui.ems.DUUIActor;
import duui.pipeline.v1.DUUIV1Annotator;

import java.util.List;
import java.util.Objects;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

public final class DUUIComponent extends DUUIActor {
    private final BlockingQueue<DUUINode> nodes;
    private final int capacity;

    public DUUIComponent(String id, List<DUUIV1Annotator> replicas) {
        super(id);
        Objects.requireNonNull(replicas, "replicas");
        this.nodes = new LinkedBlockingQueue<>();
        int slot = 0;
        for (DUUIV1Annotator annotator : replicas) {
            for (int i = 0; i < annotator.config().concurrency(); i++) {
                nodes.offer(new DUUINode(id + "-slot-" + slot++, annotator));
            }
        }
        this.capacity = nodes.size();
    }

    public int capacity() {
        return capacity;
    }

    public DUUINode borrowNode() throws InterruptedException {
        return nodes.take();
    }

    public void returnNode(DUUINode node) {
        nodes.offer(Objects.requireNonNull(node, "node"));
    }

    public int availableNodes() {
        return nodes.size();
    }
}
