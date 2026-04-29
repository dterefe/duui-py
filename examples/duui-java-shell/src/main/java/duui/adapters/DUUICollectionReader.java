package duui.adapters;

import duui.ems.DUUIArtifact;
import org.apache.uima.jcas.JCas;

public interface DUUICollectionReader extends DUUIReader {
    boolean hasNextCas();

    void getNextCas(DUUIArtifact<JCas> artifact) throws Exception;
}
