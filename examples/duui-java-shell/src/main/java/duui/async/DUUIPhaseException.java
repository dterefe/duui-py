package duui.async;

public final class DUUIPhaseException extends DUUIRuntimeException {
    private final DUUIPhase phase;

    public DUUIPhaseException(DUUIPhase phase, Throwable cause) {
        super(cause);
        this.phase = phase;
    }

    public DUUIPhase phase() {
        return phase;
    }
}
