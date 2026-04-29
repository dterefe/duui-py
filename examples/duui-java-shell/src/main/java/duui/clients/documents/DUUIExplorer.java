package duui.clients.documents;

import java.util.stream.Stream;

public abstract class DUUIExplorer {
    private final DUUIDirectory directory;

    protected DUUIExplorer(DUUIDirectory directory) {
        this.directory = directory;
    }

    public final DUUIDirectory directory() {
        return directory;
    }

    public abstract Stream<DUUIFile> files() throws DUUIDocumentException;

    public abstract Stream<DUUIDirectory> directories() throws DUUIDocumentException;

    public abstract DUUIExplorer enter(DUUIDirectory directory) throws DUUIDocumentException;

    public abstract DUUIExplorer parent() throws DUUIDocumentException;

    public abstract DUUIExplorer same();

    public abstract Stream<DUUIExplorer> breadthFirst() throws DUUIDocumentException;

    public abstract Stream<DUUIExplorer> depthFirst() throws DUUIDocumentException;
}
