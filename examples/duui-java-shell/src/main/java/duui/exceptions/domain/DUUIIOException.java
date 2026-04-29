package duui.exceptions.domain;

import java.io.IOException;

public class DUUIIOException extends DUUICheckedDomainException {
    public DUUIIOException(String message, IOException cause) {
        super(message, cause);
    }

    public DUUIIOException(IOException cause) {
        super(cause);
    }

    public IOException ioCause() {
        return (IOException) getCause();
    }
}
