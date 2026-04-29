package duui.monitoring.logging;

import duui.monitoring.model.DUUILog;
import duui.monitoring.model.DUUILogLevel;
import duui.monitoring.model.DUUIScope;

import java.util.Map;
import java.util.Objects;

public final class DUUILogger {
    private final DUUIEventEmitter emitter;
    private final String name;

    public DUUILogger(DUUIEventEmitter emitter, String name) {
        this.emitter = Objects.requireNonNull(emitter, "emitter");
        this.name = Objects.requireNonNull(name, "name");
    }

    public void debug(String message) {
        log(DUUILogLevel.DEBUG, message, Map.of());
    }

    public void info(String message) {
        log(DUUILogLevel.INFO, message, Map.of());
    }

    public void warn(String message) {
        log(DUUILogLevel.WARN, message, Map.of());
    }

    public void error(String message) {
        log(DUUILogLevel.ERROR, message, Map.of());
    }

    public void log(DUUILogLevel level, String message, Map<String, String> fields) {
        DUUIScope scope = DUUILogContext.currentScope().orElse(null);
        Map<String, String> context = scope == null ? Map.of() : scope.context();
        emitter.emit(
            new DUUILog(
                null,
                null,
                name,
                scope,
                context,
                level,
                message,
                fields
            )
        );
    }
}
