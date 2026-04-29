package duui.exceptions.domain;

public class DUUICheckedDomainException extends DUUIDomainException {
    public DUUICheckedDomainException(String message, Exception cause) {
        super(message, cause);
    }

    public DUUICheckedDomainException(Exception cause) {
        super(cause);
    }
}
