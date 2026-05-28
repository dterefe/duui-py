package duui.clients.hosts.virtualization;

import com.github.dockerjava.core.DefaultDockerClientConfig;
import com.github.dockerjava.core.DockerClientImpl;
import duui.clients.handle.DUUIAddress;

public final class DUUIPodmanClient extends DUUIDockerClient {
    public DUUIPodmanClient() {
        this(defaultPodmanHost());
    }

    public DUUIPodmanClient(String podmanHost) {
        super(
            DockerClientImpl.getInstance(
                DefaultDockerClientConfig.createDefaultConfigBuilder()
                    .withDockerHost(podmanHost)
                    .build()
            ),
            DUUIAddress.parse("podman://local")
        );
    }

    private static String defaultPodmanHost() {
        return "unix:///run/podman/podman.sock";
    }

    @Override
    protected DUUIAddress imageAddress(String reference) {
        return new DUUIAddress("podman-image", null, "/" + reference, null, null);
    }

    @Override
    protected DUUIAddress containerAddress(String id) {
        return new DUUIAddress("podman-container", null, "/" + id, null, null);
    }
}
