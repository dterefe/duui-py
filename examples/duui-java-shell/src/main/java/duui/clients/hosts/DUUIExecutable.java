package duui.clients.hosts;

import duui.clients.handle.DUUIProxy;

public interface DUUIExecutable extends DUUIProxy {
    DUUIProcess run(String... args) throws Exception;
}
