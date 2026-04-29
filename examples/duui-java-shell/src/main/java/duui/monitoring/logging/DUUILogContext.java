package duui.monitoring.logging;

import duui.monitoring.model.DUUIScope;
import duui.runtime.DUUIWorker;

import java.util.Optional;

public final class DUUILogContext {
    private DUUILogContext() {
    }

    public static void push(DUUIScope scope) {
        DUUIWorker.current().pushScope(scope);
    }

    public static void pop() {
        DUUIWorker.current().popScope();
    }

    public static Optional<DUUIScope> currentScope() {
        return DUUIWorker.currentOptional().flatMap(DUUIWorker::currentScope);
    }
}
