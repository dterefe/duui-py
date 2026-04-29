package duui.exceptions.domain;

public class DUUIInterruptedException extends DUUICheckedDomainException {
    public DUUIInterruptedException(String message, InterruptedException cause) {
        super(message, cause);
    }

    public DUUIInterruptedException(InterruptedException cause) {
        super(cause);
    }

    public InterruptedException interruptedCause() {
        return (InterruptedException) getCause();
    }
}
