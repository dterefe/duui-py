package duui.async;

public final class DUUIErrorHandler {
    public RuntimeException handle(DUUIInvocation invocation, DUUIPhase phase, DUUIPolicy policy, Throwable failure) {
        if (failure instanceof RuntimeException runtimeException) {
            return runtimeException;
        }
        return new DUUIPhaseException(phase, failure);
    }
}
