package duui.exceptions;

import duui.exceptions.domain.DUUIDomainException;

public class DUUIException extends RuntimeException {
    public DUUIException(DUUIDomainException cause) {
        super(cause);
    }

    public DUUIException(String message, DUUIDomainException cause) {
        super(message, cause);
    }
}
