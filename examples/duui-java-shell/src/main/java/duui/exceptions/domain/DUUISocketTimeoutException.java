package duui.exceptions.domain;

import java.net.SocketTimeoutException;

public class DUUISocketTimeoutException extends DUUIIOException {
    public DUUISocketTimeoutException(String message, SocketTimeoutException cause) {
        super(message, cause);
    }

    public DUUISocketTimeoutException(SocketTimeoutException cause) {
        super(cause);
    }

    public SocketTimeoutException socketTimeoutCause() {
        return (SocketTimeoutException) getCause();
    }
}
