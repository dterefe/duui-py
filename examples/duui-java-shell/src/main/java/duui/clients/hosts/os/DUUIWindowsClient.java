package duui.clients.hosts.os;

import duui.clients.hosts.DUUISystemClient;
import duui.clients.handle.DUUIAddress;
import duui.clients.hosts.DUUIExecutable;
import duui.clients.hosts.DUUIProcess;

public final class DUUIWindowsClient implements DUUISystemClient {
    @Override
    public DUUIExecutable executable(String pathOrRef) {
        return new LocalExecutable(pathOrRef);
    }

    private record LocalExecutable(String value) implements DUUIExecutable {
        @Override
        public DUUIAddress address() {
            return new DUUIAddress("file", null, java.nio.file.Path.of(value).toAbsolutePath().toString(), null, null);
        }

        @Override
        public DUUIProcess run(String... args) {
            return new LocalProcess(value);
        }
    }

    private record LocalProcess(String value) implements DUUIProcess {
        @Override
        public DUUIAddress address() {
            return new DUUIAddress("file", null, java.nio.file.Path.of(value).toAbsolutePath().toString(), null, null);
        }

        @Override
        public boolean isRunning() {
            return false;
        }

        @Override
        public void stop() {
        }
    }
}
