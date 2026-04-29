package duui.ems;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DUUIEntityModelTest {
    @Test
    void artifactCarriesTypedPayloadAndMetadata() {
        DUUIArtifact<String> artifact = new DUUIArtifact<>("artifact", "hello");
        artifact.metadata("lang", "en");
        artifact.record("PROCESS", "annotator");

        assertEquals("hello", artifact.value());
        assertEquals("en", artifact.metadata("lang", String.class).orElseThrow());
        assertEquals(1, artifact.history().size());
    }

    @Test
    void actorAndSubjectSplitRemainDistinct() {
        DUUIActor actor = new DUUIActor("actor") { };
        DUUISubject<String> subject = new DUUISubject<>("subject", "value");

        assertTrue(actor instanceof DUUIEntity);
        assertFalse(DUUISubject.class.isInstance(actor));
        assertEquals("value", subject.value());
    }
}
