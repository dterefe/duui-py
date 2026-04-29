package duui.exceptions;

import duui.exceptions.domain.DUUIDomainException;

public class DUUIValidationException extends DUUIException {
    public DUUIValidationException(DUUIDomainException cause) {
        super(cause);
    }

    public DUUIValidationException(String message, DUUIDomainException cause) {
        super(message, cause);
    }
}
