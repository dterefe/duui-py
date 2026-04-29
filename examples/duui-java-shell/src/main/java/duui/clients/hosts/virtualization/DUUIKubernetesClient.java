package duui.clients.hosts.virtualization;

import duui.clients.handle.DUUIAddress;
import io.fabric8.kubernetes.api.model.ContainerBuilder;
import io.fabric8.kubernetes.api.model.Pod;
import io.fabric8.kubernetes.api.model.PodBuilder;
import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.KubernetesClientBuilder;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.stream.Stream;

public final class DUUIKubernetesClient extends DUUIVirtualizationClient<DUUIKubernetesClient.KubernetesContainer, DUUIKubernetesClient.Image> {
    private final KubernetesClient kubernetes;
    private final String namespace;

    public DUUIKubernetesClient() {
        this(new KubernetesClientBuilder().build());
    }

    public DUUIKubernetesClient(KubernetesClient kubernetes) {
        super(DUUIAddress.parse("kubernetes://cluster"));
        this.kubernetes = kubernetes;
        this.namespace = kubernetes.getNamespace() == null ? "default" : kubernetes.getNamespace();
    }

    @Override
    public Image image(String reference) {
        return new Image(new DUUIAddress("kubernetes-image", namespace, "/" + reference, null, null), reference, 0L, null);
    }

    @Override
    public KubernetesContainer container(String id) throws DUUIVirtualizationException {
        try {
            Pod pod = kubernetes.pods().inNamespace(namespace).withName(id).get();
            if (pod == null) {
                throw new IllegalArgumentException("Pod not found: " + id);
            }
            return containerFrom(pod);
        } catch (RuntimeException e) {
            throw new DUUIContainerInspectException("Failed to inspect Kubernetes pod " + id, e);
        }
    }

    @Override
    public Stream<KubernetesContainer> containers() throws DUUIVirtualizationException {
        try {
            return kubernetes.pods().inNamespace(namespace).list().getItems().stream().map(this::containerFrom);
        } catch (RuntimeException e) {
            throw new DUUIContainerInspectException("Failed to list Kubernetes pods", e);
        }
    }

    public DUUIKubernetes cluster(String name) {
        return new Cluster(new DUUIAddress("kubernetes", namespace, "/" + name, null, null), name);
    }

    private KubernetesContainer containerFrom(Pod pod) {
        String name = pod.getMetadata().getName();
        String image = pod.getSpec().getContainers().isEmpty()
            ? "unknown"
            : pod.getSpec().getContainers().getFirst().getImage();
        Instant createdAt = pod.getMetadata().getCreationTimestamp() == null
            ? null
            : Instant.parse(pod.getMetadata().getCreationTimestamp());
        return new KubernetesContainer(
            new DUUIAddress("kubernetes-pod", namespace, "/" + name, null, null),
            name,
            image(image),
            createdAt
        );
    }

    public final class Image extends DUUIContainerImage {
        private Image(DUUIAddress address, String reference, long size, Instant createdAt) {
            super(address, reference, size, createdAt);
        }

        @Override
        public KubernetesContainer run(List<String> command) throws DUUIVirtualizationException {
            String podName = "duui-" + UUID.randomUUID();
            try {
                Pod pod = new PodBuilder()
                    .withNewMetadata()
                    .withName(podName)
                    .endMetadata()
                    .withNewSpec()
                    .withRestartPolicy("Never")
                    .withContainers(new ContainerBuilder()
                        .withName("main")
                        .withImage(reference())
                        .withCommand(command)
                        .build())
                    .endSpec()
                    .build();
                return containerFrom(kubernetes.pods().inNamespace(namespace).resource(pod).create());
            } catch (RuntimeException e) {
                throw new DUUIContainerRunException("Failed to run Kubernetes image " + reference(), e);
            }
        }

        @Override
        public DUUIContainerImage pull() {
            return this;
        }

        @Override
        public DUUIContainerImage push() throws DUUIVirtualizationException {
            throw new DUUIVirtualizationUnsupportedOperationException("Kubernetes does not push images");
        }

        @Override
        public DUUIContainerImage build(String context) throws DUUIVirtualizationException {
            throw new DUUIVirtualizationUnsupportedOperationException("Kubernetes does not build images");
        }
    }

    public final class KubernetesContainer extends DUUIContainer {
        private KubernetesContainer(DUUIAddress address, String id, DUUIContainerImage image, Instant createdAt) {
            super(address, id, image, createdAt);
        }

        @Override
        public boolean running() throws DUUIVirtualizationException {
            try {
                Pod pod = kubernetes.pods().inNamespace(namespace).withName(id()).get();
                return pod != null && "Running".equals(pod.getStatus().getPhase());
            } catch (RuntimeException e) {
                throw new DUUIContainerInspectException("Failed to inspect Kubernetes pod " + id(), e);
            }
        }

        @Override
        public DUUIContainer start() throws DUUIVirtualizationException {
            throw new DUUIVirtualizationUnsupportedOperationException("Kubernetes pods cannot be started after creation");
        }

        @Override
        public DUUIContainer stop() throws DUUIVirtualizationException {
            delete();
            return this;
        }

        @Override
        public DUUIContainer restart() throws DUUIVirtualizationException {
            throw new DUUIVirtualizationUnsupportedOperationException("Kubernetes pod restart is controller-managed");
        }

        @Override
        public void delete() throws DUUIVirtualizationException {
            try {
                kubernetes.pods().inNamespace(namespace).withName(id()).delete();
            } catch (RuntimeException e) {
                throw new DUUIContainerDeleteException("Failed to delete Kubernetes pod " + id(), e);
            }
        }
    }

    private final class Cluster extends DUUIKubernetes {
        private Cluster(DUUIAddress address, String name) {
            super(address, name);
        }

        @Override
        public Stream<DUUIContainer> containers() throws DUUIVirtualizationException {
            return DUUIKubernetesClient.this.containers().map(container -> container);
        }
    }
}
