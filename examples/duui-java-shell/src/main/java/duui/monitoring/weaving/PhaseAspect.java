package duui.monitoring.weaving;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;

import java.util.Map;

@Aspect
public final class PhaseAspect {
    @Around("@annotation(phase)")
    public Object around(ProceedingJoinPoint joinPoint, Phase phase) throws Throwable {
        String name = joinPoint.getSignature().toShortString();
        return DUUIPhaseExecutor.execute(
            name,
            phase.status(),
            phase.dispatch(),
            Map.of("method", joinPoint.getSignature().toLongString()),
            joinPoint::proceed
        );
    }
}
