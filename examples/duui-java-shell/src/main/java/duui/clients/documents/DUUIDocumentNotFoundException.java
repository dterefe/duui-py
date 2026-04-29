package duui.clients.documents;

public final class DUUIDocumentNotFoundException extends DUUIDocumentException {
    public DUUIDocumentNotFoundException(String message) {
        super(message);
    }

    public DUUIDocumentNotFoundException(String message, Throwable cause) {
        super(message, cause);
    }
}
