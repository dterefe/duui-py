package duui.adapters;

import duui.clients.documents.DUUIExplorer;
import duui.clients.documents.DUUIFile;
import duui.clients.documents.DUUIDocumentException;

import java.util.stream.Stream;

public final class DUUIDiscoveryReader implements DUUIReader {
    private final DUUIExplorer explorer;

    public DUUIDiscoveryReader(DUUIExplorer explorer) {
        this.explorer = explorer;
    }

    @Override
    public String name() {
        return "discovery";
    }

    public Stream<DUUIFile> files() throws DUUIDocumentException {
        return explorer.files();
    }
}
