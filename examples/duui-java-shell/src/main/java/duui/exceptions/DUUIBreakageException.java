package duui.exceptions;

import duui.exceptions.domain.DUUIDomainException;

public class DUUIBreakageException extends DUUIException {
    public DUUIBreakageException(DUUIDomainException cause) {
        super(cause);
    }

    public DUUIBreakageException(String message, DUUIDomainException cause) {
        super(message, cause);
    }
}
