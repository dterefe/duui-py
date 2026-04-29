package duui.clients.documents;

public final class DUUIDocumentAccessDeniedException extends DUUIDocumentException {
    public DUUIDocumentAccessDeniedException(String message) {
        super(message);
    }

    public DUUIDocumentAccessDeniedException(String message, Throwable cause) {
        super(message, cause);
    }
}
