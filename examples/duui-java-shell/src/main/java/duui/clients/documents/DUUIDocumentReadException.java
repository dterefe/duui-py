package duui.clients.documents;

public final class DUUIDocumentReadException extends DUUIDocumentException {
    public DUUIDocumentReadException(String message) {
        super(message);
    }

    public DUUIDocumentReadException(String message, Throwable cause) {
        super(message, cause);
    }
}
