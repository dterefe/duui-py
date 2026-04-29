package duui.async;

public class DUUIRuntimeException extends RuntimeException {
    public DUUIRuntimeException(String message) {
        super(message);
    }

    public DUUIRuntimeException(String message, Throwable cause) {
        super(message, cause);
    }

    public DUUIRuntimeException(Throwable cause) {
        super(cause);
    }
}
