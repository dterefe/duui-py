package duui.clients.hosts.virtualization;

import duui.clients.handle.DUUIAddress;

public abstract class DUUIKubernetes extends DUUICluster<DUUIContainer> {
    protected DUUIKubernetes(DUUIAddress address, String name) {
        super(address, name);
    }
}
