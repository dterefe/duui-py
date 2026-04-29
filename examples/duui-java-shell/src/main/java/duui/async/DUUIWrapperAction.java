package duui.async;

public interface DUUIWrapperAction {
    default void before(DUUIInvocation invocation, DUUIPhase phase) {
    }

    default void success(DUUIInvocation invocation, DUUIPhase phase) {
    }

    default void failure(DUUIInvocation invocation, DUUIPhase phase, Throwable failure) {
    }

    default void cleanup(DUUIInvocation invocation, DUUIPhase phase) {
    }
}
