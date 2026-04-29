package duui.clients.documents;

public sealed abstract class DUUIDocumentException extends Exception
    permits DUUIDocumentAccessDeniedException,
    DUUIDocumentAlreadyExistsException,
    DUUIDocumentCopyException,
    DUUIDocumentDeleteException,
    DUUIDocumentMetadataException,
    DUUIDocumentMoveException,
    DUUIDocumentNotFoundException,
    DUUIDocumentReadException,
    DUUIDocumentTraversalException,
    DUUIDocumentTypeMismatchException,
    DUUIDocumentUnsupportedOperationException,
    DUUIDocumentWriteException {
    protected DUUIDocumentException(String message) {
        super(message);
    }

    protected DUUIDocumentException(String message, Throwable cause) {
        super(message, cause);
    }
}
