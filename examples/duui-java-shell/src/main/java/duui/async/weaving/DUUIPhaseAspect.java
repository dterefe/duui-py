package duui.async.weaving;

import duui.async.DUUIPhaseBody;
import duui.async.Async;
import duui.async.DUUIEntity;
import duui.async.DUUIWorker;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;

import java.lang.reflect.Method;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.Set;

@Aspect
public final class DUUIPhaseAspect {
    private static final ThreadLocal<Set<Method>> PROCEEDING = ThreadLocal.withInitial(HashSet::new);

    @Around("@annotation(async)")
    public Object aroundPhasefulMethod(ProceedingJoinPoint joinPoint, Async async) {
        Method method = ((MethodSignature) joinPoint.getSignature()).getMethod();
        if (PROCEEDING.get().contains(method)) {
            try {
                return joinPoint.proceed();
            } catch (Throwable throwable) {
                throw sneaky(throwable);
            }
        }

        DUUIWorker worker = DUUIWorker.requireCurrent();
        DUUIPhaseBody<Void> body = () -> {
            Set<Method> proceeding = PROCEEDING.get();
            proceeding.add(method);
            try {
                joinPoint.proceed();
            } finally {
                proceeding.remove(method);
            }
        };
        worker.runtime().wrapper().invoke(
                method.getDeclaringClass(),
                method,
                async,
                entities(joinPoint.getTarget(), joinPoint.getArgs()),
                body
        );
        return null;
    }

    @SuppressWarnings("unchecked")
    private static <T extends Throwable> RuntimeException sneaky(Throwable throwable) throws T {
        throw (T) throwable;
    }

    private static Set<DUUIEntity> entities(Object owner, Object[] args) {
        LinkedHashSet<DUUIEntity> entities = new LinkedHashSet<>();
        if (owner instanceof DUUIEntity entity) {
            entities.add(entity);
        }
        if (args != null) {
            for (Object arg : args) {
                if (arg instanceof DUUIEntity entity) {
                    entities.add(entity);
                }
            }
        }
        return Set.copyOf(entities);
    }
}
