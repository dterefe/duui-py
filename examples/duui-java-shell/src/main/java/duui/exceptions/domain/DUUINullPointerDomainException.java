package duui.exceptions.domain;

public class DUUINullPointerDomainException extends DUUIRuntimeDomainException {
    public DUUINullPointerDomainException(String message, NullPointerException cause) {
        super(message, cause);
    }

    public DUUINullPointerDomainException(NullPointerException cause) {
        super(cause);
    }

    public NullPointerException nullPointerCause() {
        return (NullPointerException) getCause();
    }
}
