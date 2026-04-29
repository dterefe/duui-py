package duui.scheduler;

import duui.clients.http.DUUIHttpEndpoint;
import duui.communication.DUUICommunicationLayer;
import duui.ems.DUUIArtifact;
import duui.pipeline.DUUIComponent;
import duui.pipeline.DUUIMonoStage;
import duui.pipeline.DUUIPipeline;
import duui.pipeline.DUUIProcessorCheckpoint;
import duui.pipeline.DUUISourceCheckpoint;
import duui.pipeline.DUUITargetCheckpoint;
import duui.pipeline.v1.DUUIV1Annotator;
import duui.pipeline.v1.DUUIV1Config;
import duui.runtime.DUUIComposer;
import org.apache.uima.UIMAFramework;
import org.apache.uima.fit.factory.JCasFactory;
import org.apache.uima.jcas.JCas;
import org.junit.jupiter.api.Test;

import java.net.URI;
import java.net.http.HttpClient;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DUUISchedulerFlowTest {
    @Test
    void nextReturnsTypedStepsAndDirectorProducesSubmission() throws Exception {
        DUUIComponent component = new DUUIComponent("component", List.of(stubAnnotator()));
        DUUIMonoStage stage = new DUUIMonoStage("stage", component);
        DUUISourceCheckpoint source = new DUUISourceCheckpoint("source", stage);
        DUUIProcessorCheckpoint processor = new DUUIProcessorCheckpoint("processor", stage);
        DUUITargetCheckpoint target = new DUUITargetCheckpoint("target");
        DUUIPipeline pipeline = new DUUIPipeline().add(source).add(processor).add(target);
        DUUIComposer composer = new DUUIComposer(pipeline);
        DUUIScheduler scheduler = new DUUIScheduler(composer.pipeline());
        DUUIDirector director = new DUUIDirector(DUUISchedulerPolicy.standard());

        source.offer(new DUUIArtifact<>("artifact", JCasFactory.createJCas()));
        scheduler.markSourceDrained();

        DUUIScheduler.Step first = scheduler.next();
        assertTrue(first instanceof DUUIScheduler.SourceCheckpointStep);

        DUUISubmission submission = director.dispatch(first);
        try (DUUIGovernor<DUUIPipeline> governor = new DUUIGovernor<>(pipeline)) {
            governor.register(submission);
            submission.completionFuture().join();
            assertEquals(1, governor.submissions().size());
        }

        DUUIScheduler.Step second = scheduler.next();
        assertTrue(second instanceof DUUIScheduler.ProcessorCheckpointStep);
    }

    private static DUUIV1Annotator stubAnnotator() {
        return new DUUIV1Annotator(
            "annotator",
            new DUUIHttpEndpoint(URI.create("http://localhost"), HttpClient.newHttpClient()),
            new DUUIV1Config(1, "_InitialView", "_InitialView", Map.of()),
            new DUUIV1Annotator.Documentation("annotator", "1", "stub", "java", Map.of(), Map.of()),
            UIMAFramework.getResourceSpecifierFactory().createTypeSystemDescription(),
            new DUUICommunicationLayer() {
                @Override
                public void serialize(JCas sourceCas, java.io.OutputStream output, Map<String, String> parameters, String sourceView) {
                }

                @Override
                public void deserialize(JCas targetCas, java.io.InputStream input, String targetView) {
                }

                @Override
                public DUUICommunicationLayer copy() {
                    return this;
                }
            },
            cas -> cas.setDocumentText("processed")
        );
    }
}
