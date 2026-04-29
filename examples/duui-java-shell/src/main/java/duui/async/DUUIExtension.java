package duui.async;

import java.util.List;

public interface DUUIExtension {
    List<DUUIWrapperAction> actions(DUUIInvocation invocation, DUUIResolvedConfiguration configuration);
}
