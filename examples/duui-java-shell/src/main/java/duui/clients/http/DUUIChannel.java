package duui.clients.http;

import java.net.http.HttpRequest;
import java.util.Objects;

public final class DUUIChannel<T> {
    @FunctionalInterface
    public interface ResponseApplier<T> {
        T apply(T value, java.io.InputStream input) throws Exception;
    }

    private final IDUUIEndpoint endpoint;
    private final DUUIHttpMethod method;
    private final String route;
    private final DUUISerializer<T> serializer;
    private final ResponseApplier<T> deserializer;

    public DUUIChannel(
        IDUUIEndpoint endpoint,
        DUUIHttpMethod method,
        String route,
        DUUISerializer<T> serializer,
        ResponseApplier<T> deserializer
    ) {
        this.endpoint = Objects.requireNonNull(endpoint, "endpoint");
        this.method = Objects.requireNonNull(method, "method");
        this.route = Objects.requireNonNull(route, "route");
        this.serializer = Objects.requireNonNull(serializer, "serializer");
        this.deserializer = Objects.requireNonNull(deserializer, "deserializer");
    }

    public T request(T value) throws Exception {
        DUUIRelay<T> requestRelay = new DUUIRelay<>();
        serializer.serialize(value, requestRelay.outputStream());
        requestRelay.outputStream().close();

        DUUIRelay<T> responseRelay = new DUUIRelay<>();
        DUUIBodyHandler<T> handler = new DUUIBodyHandler<>(responseRelay, input -> deserializer.apply(value, input));

        HttpRequest request = HttpRequest.newBuilder()
            .uri(endpoint.uri().resolve(route))
            .method(method.name(), HttpRequest.BodyPublishers.ofInputStream(requestRelay::inputStream))
            .build();

        endpoint.client().send(request, handler);
        return responseRelay.future().join();
    }
}
