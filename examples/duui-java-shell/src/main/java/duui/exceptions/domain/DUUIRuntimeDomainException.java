package duui.exceptions.domain;

public class DUUIRuntimeDomainException extends DUUIDomainException {
    public DUUIRuntimeDomainException(String message, RuntimeException cause) {
        super(message, cause);
    }

    public DUUIRuntimeDomainException(RuntimeException cause) {
        super(cause);
    }
}
