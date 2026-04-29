package duui.monitoring.weaving;

import duui.monitoring.model.DUUIDispatchMode;
import duui.monitoring.model.DUUIStatus;
import duui.monitoring.telemetry.DUUIPhaseSession;
import duui.monitoring.telemetry.DUUITelemetryService;

import java.util.Map;

public final class DUUIPhaseExecutor {
    private DUUIPhaseExecutor() {
    }

    @FunctionalInterface
    public interface PhaseCallable<T> {
        T call() throws Throwable;
    }

    public static <T> T execute(
        String name,
        DUUIStatus status,
        DUUIDispatchMode dispatch,
        Map<String, String> context,
        PhaseCallable<T> callable
    ) throws Throwable {
        DUUITelemetryService telemetry = DUUITelemetryService.get();
        DUUIPhaseSession session = telemetry.beginPhase(name, status, dispatch, context);
        try {
            T result = callable.call();
            telemetry.endPhase(session);
            return result;
        } catch (Throwable error) {
            telemetry.failPhase(session, error);
            throw error;
        }
    }
}
