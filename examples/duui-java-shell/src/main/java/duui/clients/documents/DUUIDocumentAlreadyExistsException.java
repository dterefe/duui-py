package duui.clients.documents;

public final class DUUIDocumentAlreadyExistsException extends DUUIDocumentException {
    public DUUIDocumentAlreadyExistsException(String message) {
        super(message);
    }

    public DUUIDocumentAlreadyExistsException(String message, Throwable cause) {
        super(message, cause);
    }
}
