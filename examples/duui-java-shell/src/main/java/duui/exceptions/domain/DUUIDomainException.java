package duui.exceptions.domain;

public class DUUIDomainException extends Exception {
    public DUUIDomainException(String message, Throwable cause) {
        super(message, cause);
    }

    public DUUIDomainException(Throwable cause) {
        super(cause);
    }
}
