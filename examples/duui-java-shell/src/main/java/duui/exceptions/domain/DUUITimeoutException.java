package duui.exceptions.domain;

import java.util.concurrent.TimeoutException;

public class DUUITimeoutException extends DUUICheckedDomainException {
    public DUUITimeoutException(String message, TimeoutException cause) {
        super(message, cause);
    }

    public DUUITimeoutException(TimeoutException cause) {
        super(cause);
    }

    public TimeoutException timeoutCause() {
        return (TimeoutException) getCause();
    }
}
