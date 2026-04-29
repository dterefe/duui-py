package duui.async;

import java.util.Objects;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public final class DUUIDispatcher {
    private final DUUIExecutors executors;

    public DUUIDispatcher(DUUIExecutors executors) {
        this.executors = Objects.requireNonNull(executors, "executors");
    }

    public <T> DUUISubmission<T> dispatch(DUUIPhase phase, DUUIPolicy policy, Callable<T> body) {
        ExecutorService executor = executors.executor(policy.execution().mode());
        Future<T> future = executor.submit(body);
        return new DUUISubmission<>(phase, future);
    }

    public <T> T await(DUUISubmission<T> submission, DUUIPolicy policy) {
        try {
            if (policy.execution().timeout() == null) {
                return submission.future().get();
            }
            return submission.future().get(policy.execution().timeout().toMillis(), TimeUnit.MILLISECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new DUUIRuntimeException("interrupted while awaiting DUUI phase", e);
        } catch (TimeoutException e) {
            submission.future().cancel(true);
            throw new DUUIRuntimeException("DUUI phase timed out: " + submission.phase().duuiId().name(), e);
        } catch (ExecutionException e) {
            Throwable cause = e.getCause();
            if (cause instanceof RuntimeException runtimeException) {
                throw runtimeException;
            }
            throw new DUUIRuntimeException(cause);
        }
    }
}
