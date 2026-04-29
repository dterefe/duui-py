package duui.scheduler;

import duui.ems.DUUIArtifact;
import duui.pipeline.DUUICheckpoint;
import duui.pipeline.DUUIComponent;
import duui.pipeline.DUUINode;
import duui.pipeline.DUUIProcessorCheckpoint;
import duui.pipeline.DUUIStage;
import duui.runtime.DUUIWorker;
import org.apache.uima.jcas.JCas;

import java.util.List;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

public final class DUUIDirector {
    private final DUUISchedulerPolicy policy;

    public DUUIDirector(DUUISchedulerPolicy policy) {
        this.policy = policy == null ? DUUISchedulerPolicy.standard() : policy;
    }

    public DUUISubmission dispatch(DUUIScheduler.Step step) {
        if (step instanceof DUUIScheduler.TargetCheckpointStep targetStep) {
            CompletableFuture<DUUIArtifact<?>> future = CompletableFuture.completedFuture(targetStep.artifact());
            return new DUUISubmission(
                UUID.randomUUID().toString(),
                targetStep.checkpoint(),
                null,
                null,
                targetStep.artifact(),
                future,
                () -> future.cancel(true)
            );
        }
        if (step instanceof DUUIScheduler.SourceCheckpointStep sourceStep) {
            return submit(sourceStep.source(), sourceStep.target(), sourceStep.target().stage(), sourceStep.artifact());
        }
        if (step instanceof DUUIScheduler.ProcessorCheckpointStep processorStep) {
            DUUIStage stage = processorStep.source().stage();
            return submit(processorStep.source(), processorStep.target(), stage, processorStep.artifact());
        }
        throw new IllegalArgumentException("Unsupported step for dispatch: " + step);
    }

    @SuppressWarnings("unchecked")
    private DUUISubmission submit(DUUICheckpoint source, DUUICheckpoint target, DUUIStage stage, DUUIArtifact<?> artifact) {
        List<DUUIComponent> components = policy.stageDispatchPolicy().select(stage);
        CompletableFuture<DUUIArtifact<?>> future = CompletableFuture.supplyAsync(
            () -> {
                try {
                    switch (stage.shape()) {
                        case MONO -> executeComponent(components.getFirst(), (DUUIArtifact<JCas>) artifact);
                        case LINEAR -> {
                            for (DUUIComponent component : components) {
                                executeComponent(component, (DUUIArtifact<JCas>) artifact);
                            }
                        }
                        case PARALLEL -> CompletableFuture.allOf(
                            components.stream()
                                .map(component -> CompletableFuture.runAsync(
                                    () -> executeUnchecked(component, (DUUIArtifact<JCas>) artifact),
                                    DUUIWorker.current().virtualExecutor("duui-stage")
                                ))
                                .toArray(CompletableFuture[]::new)
                        ).join();
                    }
                    target.offer(artifact);
                    return artifact;
                } catch (Exception error) {
                    throw new RuntimeException(error);
                }
            },
            DUUIWorker.current().virtualExecutor("duui-director")
        );

        return new DUUISubmission(
            UUID.randomUUID().toString(),
            source,
            stage,
            null,
            artifact,
            future,
            () -> future.cancel(true)
        );
    }

    private void executeUnchecked(DUUIComponent component, DUUIArtifact<JCas> artifact) {
        try {
            executeComponent(component, artifact);
        } catch (Exception error) {
            throw new RuntimeException(error);
        }
    }

    private void executeComponent(DUUIComponent component, DUUIArtifact<JCas> artifact) throws Exception {
        DUUINode node = component.borrowNode();
        try {
            node.process(artifact);
        } finally {
            component.returnNode(node);
        }
    }
}
