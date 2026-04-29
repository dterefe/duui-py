package duui.async;

@FunctionalInterface
public interface DUUIPhaseBody<T> {
    void call() throws Throwable;
}
