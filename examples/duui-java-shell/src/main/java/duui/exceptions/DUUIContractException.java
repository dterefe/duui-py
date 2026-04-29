package duui.exceptions;

import duui.exceptions.domain.DUUIDomainException;

public class DUUIContractException extends DUUIException {
    public DUUIContractException(DUUIDomainException cause) {
        super(cause);
    }

    public DUUIContractException(String message, DUUIDomainException cause) {
        super(message, cause);
    }
}
