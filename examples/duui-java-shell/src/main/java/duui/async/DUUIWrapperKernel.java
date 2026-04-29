package duui.async;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public final class DUUIWrapperKernel {
    public void invoke(Class<?> ownerType, Method method, Async annotation, Set<DUUIEntity> entities, DUUIPhaseBody<?> body) {
        DUUIWorker worker = DUUIWorker.current();
        if (worker == null) {
            invokeOutsideWorker(annotation, body);
            return;
        }

        DUUIRuntime runtime = worker.runtime();
        DUUIInvocation invocation = runtime.phases().invocation(ownerType, method, annotation, worker, entities);
        DUUIPhase phase = runtime.phases().phase(invocation);
        DUUIPolicy policy = runtime.policies().resolve(invocation);
        List<DUUIWrapperAction> actions = new ArrayList<>(policy.actions());

        runtime.registry().registerPhase(phase);
        phase.transition(DUUILifecycle.INACTIVE);

        DUUISubmission<Void> submission = runtime.dispatcher().dispatch(phase, policy, () -> {
            DUUIWorker executionWorker = DUUIWorker.requireCurrent();
            executionWorker.context().push(phase);
            for (DUUIWrapperAction action : actions) {
                action.before(invocation, phase);
            }
            try {
                phase.transition(DUUILifecycle.ACTIVE);
                body.call();
                for (DUUIWrapperAction action : actions) {
                    action.success(invocation, phase);
                }
                phase.transition(DUUILifecycle.TERMINAL);
                return null;
            } catch (Throwable failure) {
                phase.transition(DUUILifecycle.TERMINAL);
                for (DUUIWrapperAction action : actions) {
                    action.failure(invocation, phase, failure);
                }
                throw runtime.errors().handle(invocation, phase, policy, failure);
            } finally {
                for (int i = actions.size() - 1; i >= 0; i--) {
                    actions.get(i).cleanup(invocation, phase);
                }
                executionWorker.context().pop(phase);
            }
        });

        if (policy.execution().scopeMode() == DUUIScopeMode.CONCURRENT) {
            return;
        }
        runtime.dispatcher().await(submission, policy);
    }

    private void invokeOutsideWorker(Async annotation, DUUIPhaseBody<?> body) {
        try {
            body.call();
        } catch (Throwable throwable) {
            throw new DUUIRuntimeException("DUUI phase call outside worker failed: " + annotation.name(), throwable);
        }
    }
}
