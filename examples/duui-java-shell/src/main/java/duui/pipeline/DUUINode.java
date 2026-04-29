package duui.pipeline;

import duui.ems.DUUIArtifact;
import duui.monitoring.model.DUUIDispatchMode;
import duui.monitoring.model.DUUIStatus;
import duui.monitoring.weaving.DUUIPhaseExecutor;
import duui.pipeline.v1.DUUIV1Annotator;
import org.apache.uima.jcas.JCas;

import java.util.Map;

public record DUUINode(String id, DUUIV1Annotator annotator) {
    public void process(DUUIArtifact<JCas> artifact) throws Exception {
        try {
            DUUIPhaseExecutor.execute(
                "node.process",
                DUUIStatus.PROCESSING,
                DUUIDispatchMode.MIXED,
                Map.of("node", id, "annotator", annotator.id()),
                () -> {
                    annotator.process(artifact);
                    return null;
                }
            );
        } catch (RuntimeException runtimeException) {
            throw runtimeException;
        } catch (Throwable throwable) {
            if (throwable instanceof Exception exception) {
                throw exception;
            }
            throw new IllegalStateException("Unexpected throwable during node processing", throwable);
        }
    }
}
