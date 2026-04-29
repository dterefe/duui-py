package duui.exceptions.domain;

import java.net.SocketException;

public class DUUISocketException extends DUUIIOException {
    public DUUISocketException(String message, SocketException cause) {
        super(message, cause);
    }

    public DUUISocketException(SocketException cause) {
        super(cause);
    }

    public SocketException socketCause() {
        return (SocketException) getCause();
    }
}
