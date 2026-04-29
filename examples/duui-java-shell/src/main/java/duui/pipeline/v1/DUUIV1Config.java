package duui.pipeline.v1;

import java.util.Map;

public record DUUIV1Config(
    int concurrency,
    String sourceView,
    String targetView,
    Map<String, String> parameters
) {
    public DUUIV1Config {
        if (concurrency <= 0) {
            throw new IllegalArgumentException("concurrency must be greater than 0");
        }
        sourceView = sourceView == null ? "_InitialView" : sourceView;
        targetView = targetView == null ? "_InitialView" : targetView;
        parameters = parameters == null ? Map.of() : Map.copyOf(parameters);
    }
}
