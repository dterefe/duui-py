package duui.scheduler;

import duui.pipeline.DUUIPipeline;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

public final class DUUIGovernor<T extends DUUIPipeline> implements AutoCloseable {
    private final T pipeline;
    private final CopyOnWriteArrayList<Consumer<DUUISubmission>> observers = new CopyOnWriteArrayList<>();
    private final CopyOnWriteArrayList<DUUISubmission> submissions = new CopyOnWriteArrayList<>();

    public DUUIGovernor(T pipeline) {
        this.pipeline = pipeline;
    }

    public T pipeline() {
        return pipeline;
    }

    public void observe(Consumer<DUUISubmission> observer) {
        observers.add(observer);
    }

    public void register(DUUISubmission submission) {
        submissions.add(submission);
        observers.forEach(observer -> observer.accept(submission));
        submission.completionFuture().whenComplete((ignored, error) -> {
            if (error == null) {
                submission.state(DUUISubmission.State.COMPLETED);
            } else {
                submission.state(DUUISubmission.State.FAILED);
            }
        });
    }

    public List<DUUISubmission> submissions() {
        return List.copyOf(submissions);
    }

    @Override
    public void close() {
        submissions.removeIf(submission -> submission.state() == DUUISubmission.State.COMPLETED);
    }
}
