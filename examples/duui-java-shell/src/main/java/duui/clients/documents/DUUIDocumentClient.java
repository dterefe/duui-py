package duui.clients.documents;

import duui.clients.handle.DUUIAddress;

public abstract class DUUIDocumentClient {
    public abstract DUUIFile file(DUUIAddress address) throws DUUIDocumentException;

    public abstract DUUIDirectory directory(DUUIAddress address) throws DUUIDocumentException;

    public abstract DUUIExplorer explorer(DUUIDirectory directory) throws DUUIDocumentException;
}
