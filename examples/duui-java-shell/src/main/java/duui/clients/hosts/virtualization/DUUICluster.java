package duui.clients.hosts.virtualization;

import duui.clients.handle.DUUIAddress;
import duui.clients.handle.DUUIProxy;

import java.util.stream.Stream;

public abstract class DUUICluster<C extends DUUIContainer> implements DUUIProxy {
    private final DUUIAddress address;
    private final String name;

    protected DUUICluster(DUUIAddress address, String name) {
        this.address = address;
        this.name = name;
    }

    @Override
    public final DUUIAddress address() {
        return address;
    }

    public final String name() {
        return name;
    }

    public abstract Stream<C> containers() throws DUUIVirtualizationException;
}
