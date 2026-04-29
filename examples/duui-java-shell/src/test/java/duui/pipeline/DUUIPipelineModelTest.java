package duui.pipeline;

import duui.clients.http.DUUIHttpEndpoint;
import duui.communication.DUUICommunicationLayer;
import duui.ems.DUUIArtifact;
import duui.pipeline.v1.DUUIV1Annotator;
import duui.pipeline.v1.DUUIV1Config;
import org.apache.uima.fit.factory.JCasFactory;
import org.apache.uima.UIMAFramework;
import org.apache.uima.jcas.JCas;
import org.junit.jupiter.api.Test;

import java.net.URI;
import java.net.http.HttpClient;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DUUIPipelineModelTest {
    @Test
    void checkpointsPreserveQueueSemantics() throws Exception {
        DUUISourceCheckpoint source = new DUUISourceCheckpoint("source", null);
        DUUIArtifact<JCas> artifact = new DUUIArtifact<>("artifact", JCasFactory.createJCas());

        source.offer(artifact);

        assertEquals(1, source.size());
        assertTrue(source.poll().isPresent());
        assertEquals(0, source.size());
    }

    @Test
    void stageCompositionRetainsDeclaredShape() {
        DUUIComponent component = new DUUIComponent("component", List.of(stubAnnotator("a", 1)));
        assertEquals(DUUIStage.DispatchShape.MONO, new DUUIMonoStage("mono", component).shape());
        assertEquals(DUUIStage.DispatchShape.PARALLEL, new DUUIParallelStage("parallel", List.of(component)).shape());
        assertEquals(DUUIStage.DispatchShape.LINEAR, new DUUILinearStage("linear", List.of(component)).shape());
    }

    @Test
    void componentCapacityFlattensReplicasTimesConcurrency() {
        DUUIComponent component = new DUUIComponent(
            "component",
            List.of(stubAnnotator("a", 2), stubAnnotator("b", 2))
        );

        assertEquals(4, component.capacity());
        assertEquals(4, component.availableNodes());
    }

    private static DUUIV1Annotator stubAnnotator(String id, int concurrency) {
        return new DUUIV1Annotator(
            id,
            new DUUIHttpEndpoint(URI.create("http://localhost"), HttpClient.newHttpClient()),
            new DUUIV1Config(concurrency, "_InitialView", "_InitialView", Map.of()),
            new DUUIV1Annotator.Documentation(id, "1", "stub", "java", Map.of(), Map.of()),
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
            cas -> { }
        );
    }
}
