package duui.clients.documents;

public final class DUUIDocumentTypeMismatchException extends DUUIDocumentException {
    public DUUIDocumentTypeMismatchException(String message) {
        super(message);
    }

    public DUUIDocumentTypeMismatchException(String message, Throwable cause) {
        super(message, cause);
    }
}
