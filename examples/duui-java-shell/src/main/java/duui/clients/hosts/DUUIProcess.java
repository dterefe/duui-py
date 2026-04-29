package duui.clients.hosts;

import duui.clients.handle.DUUIProxy;

public interface DUUIProcess extends DUUIProxy {
    boolean isRunning();

    void stop() throws Exception;
}
