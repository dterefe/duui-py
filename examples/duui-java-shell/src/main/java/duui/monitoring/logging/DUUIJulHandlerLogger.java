package duui.monitoring.logging;

import duui.monitoring.model.DUUILog;
import duui.monitoring.model.DUUILogLevel;
import duui.monitoring.model.DUUIScope;

import java.util.Map;
import java.util.Objects;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.LogRecord;

public final class DUUIJulHandlerLogger extends Handler {
    private final DUUIEventEmitter emitter;

    public DUUIJulHandlerLogger(DUUIEventEmitter emitter) {
        this.emitter = Objects.requireNonNull(emitter, "emitter");
    }

    @Override
    public void publish(LogRecord record) {
        if (record == null || !isLoggable(record)) {
            return;
        }

        DUUIScope scope = DUUILogContext.currentScope().orElse(null);
        Map<String, String> context = scope == null ? Map.of() : scope.context();

        emitter.emit(
            new DUUILog(
                null,
                null,
                record.getLoggerName() == null ? "jul" : record.getLoggerName(),
                scope,
                context,
                toLevel(record.getLevel()),
                record.getMessage(),
                Map.of()
            )
        );
    }

    private DUUILogLevel toLevel(Level level) {
        if (level.intValue() >= Level.SEVERE.intValue()) {
            return DUUILogLevel.ERROR;
        }
        if (level.intValue() >= Level.WARNING.intValue()) {
            return DUUILogLevel.WARN;
        }
        if (level.intValue() >= Level.INFO.intValue()) {
            return DUUILogLevel.INFO;
        }
        return DUUILogLevel.DEBUG;
    }

    @Override
    public void flush() {
    }

    @Override
    public void close() {
    }
}
