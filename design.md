duui-primitives.md

```java
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.channels.Channels;
import java.nio.channels.Pipe;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;

public final class DUUIRelay<T> implements AutoCloseable {
    private volatile InputStream input;
    private volatile OutputStream output;

    private final AtomicReference<Throwable> failure = new AtomicReference<>();
    private volatile Consumer<Throwable> cancelHandler = t -> {};
    private volatile CompletableFuture<T> future;

    public DUUIRelay() throws IOException {
        reset();
    }

    public InputStream inputStream() {
        return input;
    }

    public OutputStream outputStream() {
        return output;
    }

    public CompletableFuture<T> future() {
        return future;
    }

    public void complete(T value) {
        future.complete(value);
    }

    public void onCancel(Consumer<Throwable> handler) {
        this.cancelHandler = Objects.requireNonNull(handler);
    }

    public void cancel(Throwable throwable) {
        Throwable cause = throwable == null ? new IOException("DUUI relay cancelled") : throwable;
        if (!failure.compareAndSet(null, cause)) {
            return;
        }

        future.completeExceptionally(cause);

        try {
            if (output != null) output.close();
        } catch (IOException ignored) {}
        try {
            if (input != null) input.close();
        } catch (IOException ignored) {}

        cancelHandler.accept(cause);
    }

    public void reset() throws IOException {
        failure.set(null);
        future = new CompletableFuture<>();

        Pipe pipe = Pipe.open();
        input = Channels.newInputStream(pipe.source());
        output = Channels.newOutputStream(pipe.sink());
    }

    @Override
    public void close() {
        try {
            if (output != null) output.close();
        } catch (IOException ignored) {}
        try {
            if (input != null) input.close();
        } catch (IOException ignored) {}
    }
}

```

```java
import java.io.IOException;
import java.io.OutputStream;
import java.net.http.HttpResponse;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.Flow;

public final class DUUIBodyHandler<T> implements HttpResponse.BodyHandler<T> {
    private final DUUIRelay<T> relay;

    public DUUIBodyHandler(DUUIRelay<T> relay) {
        this.relay = relay;
    }

    @Override
    public HttpResponse.BodySubscriber<T> apply(HttpResponse.ResponseInfo responseInfo) {
        return new Subscriber<>(relay);
    }

    private static final class Subscriber<T> implements HttpResponse.BodySubscriber<T> {
        private final DUUIRelay<T> relay;
        private final OutputStream output;
        private Flow.Subscription subscription;

        private Subscriber(DUUIRelay<T> relay) {
            this.relay = relay;
            this.output = relay.outputStream();
        }

        @Override
        public CompletionStage<T> getBody() {
            return relay.future();
        }

        @Override
        public void onSubscribe(Flow.Subscription subscription) {
            this.subscription = subscription;
            subscription.request(1);
        }

        @Override
        public void onNext(List<ByteBuffer> items) {
            try {
                for (ByteBuffer b : items) {
                    if (b.hasArray()) {
                        output.write(
                            b.array(),
                            b.arrayOffset() + b.position(),
                            b.remaining()
                        );
                        b.position(b.limit());
                    } else {
                        byte[] tmp = new byte[b.remaining()];
                        b.get(tmp);
                        output.write(tmp);
                    }
                }
                subscription.request(1);
            } catch (IOException e) {
                relay.cancel(e);
                subscription.cancel();
            }
        }

        @Override
        public void onError(Throwable throwable) {
            relay.cancel(throwable);
        }

        @Override
        public void onComplete() {
            try {
                output.close();
            } catch (IOException e) {
                relay.cancel(e);
            }
        }
    }
}

```

```java
import java.io.InputStream;
import org.apache.uima.jcas.JCas;

@FunctionalInterface
public interface DUUIDeserializer<T> {
    void deserialize(JCas cas, InputStream input);
}
```

```java
import java.io.OutputStream;
import org.apache.uima.jcas.JCas;

@FunctionalInterface
public interface DUUISerializer<P> {
    void serialize(JCas cas, OutputStream output);
}
```

```java
public enum DUUIHttpMethod {
    GET,
    DELETE,
    HEAD,
    OPTIONS,
    POST,
    PUT,
    PATCH
}
```

```java
import java.io.InputStream;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Objects;

public record DUUISignal<T>(
    IDUUIEndpoint endpoint,
    DUUIHttpMethod method,
    String route,
    DUUIDeserializer<T> deserializer
) {
    public DUUISignal {
        Objects.requireNonNull(endpoint, "endpoint");
        Objects.requireNonNull(method, "method");
        Objects.requireNonNull(route, "route");
        Objects.requireNonNull(deserializer, "deserializer");

        if (method != DUUIHttpMethod.GET
            && method != DUUIHttpMethod.DELETE
            && method != DUUIHttpMethod.HEAD
            && method != DUUIHttpMethod.OPTIONS) {
            throw new IllegalArgumentException("DUUISignal only supports HTTP methods without request body");
        }
    }

    public T request() throws Exception {
        DUUIRelay<T> responseRelay = new DUUIRelay<>();
        DUUIBodyHandler<T> bodyHandler = new DUUIBodyHandler<>(responseRelay);

        HttpRequest request = HttpRequest.newBuilder()
            .uri(endpoint.uri().resolve(route))
            .method(method.name(), HttpRequest.BodyPublishers.noBody())
            .build();

        endpoint.client().send(request, bodyHandler);

        try (InputStream input = responseRelay.inputStream()) {
            T value = deserializer.deserialize(input);
            responseRelay.complete(value);
        } catch (Throwable t) {
            responseRelay.cancel(t);
        }

        return responseRelay.future().join();
    }
}
```

```java
import java.io.InputStream;
import java.io.OutputStream;
import java.net.http.HttpRequest;
import java.util.Objects;

public record DUUIChannel<T>(
    IDUUIEndpoint endpoint,
    DUUIHttpMethod method,
    String route,
    DUUISerializer<T> serializer,
    DUUIDeserializer<T> deserializer
) {
    public DUUIChannel {
        Objects.requireNonNull(endpoint, "endpoint");
        Objects.requireNonNull(method, "method");
        Objects.requireNonNull(route, "route");
        Objects.requireNonNull(serializer, "serializer");
        Objects.requireNonNull(deserializer, "deserializer");

        if (method != DUUIHttpMethod.POST
            && method != DUUIHttpMethod.PUT
            && method != DUUIHttpMethod.PATCH) {
            throw new IllegalArgumentException("DUUIChannel only supports HTTP methods with request body");
        }
    }

    public T request(T payload) throws Exception {
        DUUIRelay<Void> requestRelay = new DUUIRelay<>();
        DUUIRelay<T> responseRelay = new DUUIRelay<>();
        DUUIBodyHandler<T> bodyHandler = new DUUIBodyHandler<>(responseRelay);

        try (OutputStream output = requestRelay.outputStream()) {
            serializer.serialize(payload, output);
        } catch (Throwable t) {
            requestRelay.cancel(t);
            responseRelay.cancel(t);
            return responseRelay.future().join();
        }

        HttpRequest request = HttpRequest.newBuilder()
            .uri(endpoint.uri().resolve(route))
            .method(method.name(), HttpRequest.BodyPublishers.ofInputStream(requestRelay::inputStream))
            .build();

        endpoint.client().send(request, bodyHandler);

        try (InputStream input = responseRelay.inputStream()) {
            T value = deserializer.deserialize(input);
            responseRelay.complete(value);
        } catch (Throwable t) {
            responseRelay.cancel(t);
        }

        return responseRelay.future().join();
    }
}
```

```java
package duui.clients.http;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public record DUUIHttpConfig(
    Duration timeout,
    HttpClient.Version version
) {
    public DUUIHttpConfig {
        timeout = timeout == null ? Duration.ofSeconds(30) : timeout;
        version = version == null ? HttpClient.Version.HTTP_1_1 : version;
    }

    public static DUUIHttpConfig standard() {
        return new DUUIHttpConfig(Duration.ofSeconds(30), HttpClient.Version.HTTP_1_1);
    }
}

```

```java
package duui.clients.http;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public abstract class DUUIHttpProxy {
    private final HttpClient client;
    private final URI endpoint;
    private final DUUIHttpConfig config;

    protected DUUIHttpProxy(HttpClient client, URI endpoint, DUUIHttpConfig config) {
        this.client = client;
        this.endpoint = endpoint;
        this.config = config;
    }

    public HttpClient client() {
        return client;
    }

    public URI endpoint() {
        return endpoint;
    }

    public DUUIHttpConfig config() {
        return config;
    }

    private URI resolve(String path) {
        return endpoint.resolve(path);
    }

    private HttpRequest.Builder request(String path, String... headers) {
        HttpRequest.Builder builder = HttpRequest.newBuilder()
            .uri(resolve(path))
            .timeout(config.timeout())
            .version(config.version());

        if (headers != null && headers.length > 0) {
            builder.headers(headers);
        }

        return builder;
    }

    private <T> HttpResponse<T> send(HttpRequest request, DUUIBodyHandler<T> bodyHandler) throws IOException, InterruptedException {
        return client.send(request, bodyHandler);
    }

    public <T> HttpResponse<T> get(String path, DUUIBodyHandler<T> bodyHandler, String... headers) throws IOException, InterruptedException {
        return send(request(path, headers).GET().build(), bodyHandler);
    }

    public <T> HttpResponse<T> delete(String path, DUUIBodyHandler<T> bodyHandler, String... headers) throws IOException, InterruptedException {
        return send(request(path, headers).DELETE().build(), bodyHandler);
    }

    public <T> HttpResponse<T> head(String path, DUUIBodyHandler<T> bodyHandler, String... headers) throws IOException, InterruptedException {
        return send(
            request(path, headers)
                .method("HEAD", HttpRequest.BodyPublishers.noBody())
                .build(),
            bodyHandler
        );
    }

    public <T> HttpResponse<T> options(String path, DUUIBodyHandler<T> bodyHandler, String... headers) throws IOException, InterruptedException {
        return send(
            request(path, headers)
                .method("OPTIONS", HttpRequest.BodyPublishers.noBody())
                .build(),
            bodyHandler
        );
    }

    public <T> HttpResponse<T> post(String path, DUUIRelay<Void> relay, DUUIBodyHandler<T> bodyHandler, String... headers)
        throws IOException, InterruptedException {
        return send(
            request(path, headers)
                .POST(HttpRequest.BodyPublishers.ofInputStream(relay::inputStream))
                .build(),
            bodyHandler
        );
    }

    public <T> HttpResponse<T> put(String path, DUUIRelay<Void> relay, DUUIBodyHandler<T> bodyHandler, String... headers)
        throws IOException, InterruptedException {
        return send(
            request(path, headers)
                .PUT(HttpRequest.BodyPublishers.ofInputStream(relay::inputStream))
                .build(),
            bodyHandler
        );
    }

    public <T> HttpResponse<T> patch(String path, DUUIRelay<Void> relay, DUUIBodyHandler<T> bodyHandler, String... headers)
        throws IOException, InterruptedException {
        return send(
            request(path, headers)
                .method("PATCH", HttpRequest.BodyPublishers.ofInputStream(relay::inputStream))
                .build(),
            bodyHandler
        );
    }
}
```

```java
package duui.clients.http;

import java.net.URI;
import java.net.http.HttpClient;

public interface IDUUIEndpoint {
    URI uri();

    HttpClient client();
}

```

```java
package duui.pipeline.v1;

import com.fasterxml.jackson.databind.ObjectMapper;
import duui.clients.http.DUUIChannel;
import duui.clients.http.DUUIDeserializer;
import duui.clients.http.DUUIHttpMethod;
import duui.clients.http.DUUISerializer;
import duui.clients.http.DUUISignal;
import duui.clients.http.IDUUIEndpoint;
import duui.communication.DUUICommunicationLayer;
import duui.communication.DUUILuaCommunicationLayer;
import org.apache.uima.UIMAFramework;
import org.apache.uima.cas.CASException;
import org.apache.uima.jcas.JCas;
import org.apache.uima.resource.metadata.TypeSystemDescription;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;

public final class DUUIV1Annotator {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final IDUUIEndpoint endpointHandle;
    private final DUUIV1Config config;

    private final DUUISignal<Documentation> documentationSignal;
    private final DUUISignal<TypeSystemDescription> typesystemSignal;
    private final DUUISignal<DUUICommunicationLayer> communicationLayerSignal;
    private final DUUIChannel<JCas> processChannel;

    private final Documentation documentation;
    private final TypeSystemDescription typesystem;
    private final DUUICommunicationLayer communicationLayer;

    public DUUIV1Annotator(
        IDUUIEndpoint endpoint,
        DUUIV1Config config
    ) throws Exception {
        this.endpointHandle = endpoint;
        this.config = config;

        this.documentationSignal = documentationSignal(endpoint);
        this.typesystemSignal = typesystemSignal(endpoint);
        this.communicationLayerSignal = communicationLayerSignal(endpoint);

        this.documentation = documentationSignal.request();
        this.typesystem = typesystemSignal.request();
        this.communicationLayer = communicationLayerSignal.request();

        this.processChannel = processChannel(endpoint, this.communicationLayer, config);
    }

    public DUUIV1Annotator(
        IDUUIEndpoint endpoint,
        DUUIV1Config config,
        Documentation documentation,
        TypeSystemDescription typesystem,
        DUUICommunicationLayer communicationLayer
    ) throws Exception {
        this.endpointHandle = endpoint;
        this.config = config;
        this.documentationSignal = documentationSignal(endpoint);
        this.typesystemSignal = typesystemSignal(endpoint);
        this.communicationLayerSignal = communicationLayerSignal(endpoint);
        this.documentation = documentation;
        this.typesystem = typesystem;
        this.communicationLayer = communicationLayer;
        this.processChannel = processChannel(endpoint, communicationLayer, config);
    }

    public IDUUIEndpoint endpoint() {
        return endpointHandle;
    }

    public DUUIV1Config config() {
        return config;
    }

    public Documentation documentation() {
        return documentation;
    }

    public TypeSystemDescription typesystem() {
        return typesystem;
    }

    public DUUICommunicationLayer communicationLayer() {
        return communicationLayer;
    }

    public void serialize(
        JCas cas,
        OutputStream stream,
        Map<String, String> parameters,
        String sourceView
    ) throws CASException {
        communicationLayer.serialize(cas, stream, parameters, sourceView);
    }

    public JCas analyse(JCas cas) throws Exception {
        return processChannel.request(cas);
    }

    public void deserialize(
        JCas cas,
        InputStream stream,
        String targetView
    ) throws CASException {
        communicationLayer.deserialize(cas, stream, targetView);
    }

    private DUUISignal<Documentation> documentationSignal(IDUUIEndpoint endpoint) {
        return new DUUISignal<>(endpoint, DUUIHttpMethod.GET, "/v1/documentation", documentationDeserializer());
    }

    private DUUISignal<TypeSystemDescription> typesystemSignal(IDUUIEndpoint endpoint) {
        return new DUUISignal<>(endpoint, DUUIHttpMethod.GET, "/v1/typesystem", typesystemDeserializer());
    }

    private DUUISignal<DUUICommunicationLayer> communicationLayerSignal(IDUUIEndpoint endpoint) {
        return new DUUISignal<>(endpoint, DUUIHttpMethod.GET, "/v1/communication_layer", communicationLayerDeserializer());
    }

    private DUUIChannel<JCas> processChannel(
        IDUUIEndpoint endpoint,
        DUUICommunicationLayer communicationLayer,
        DUUIV1Config config
    ) {
        return new DUUIChannel<>(
            endpoint,
            DUUIHttpMethod.POST,
            "/v1/process",
            processSerializer(communicationLayer, config),
            processDeserializer(communicationLayer, config)
        );
    }

    private DUUIDeserializer<Documentation> documentationDeserializer() {
        return input -> MAPPER.readValue(input, Documentation.class);
    }

    private DUUIDeserializer<TypeSystemDescription> typesystemDeserializer() {
        return input -> UIMAFramework.getXMLParser().parseTypeSystemDescription(new XMLInputSource(input, null));
    }

    private DUUIDeserializer<DUUICommunicationLayer> communicationLayerDeserializer() {
        return input -> new DUUILuaCommunicationLayer(new String(input.readAllBytes(), StandardCharsets.UTF_8));
    }

    private DUUISerializer<JCas> processSerializer(DUUICommunicationLayer communicationLayer, DUUIV1Config config) {
        return (cas, output) -> communicationLayer.serialize(cas, output, config.parameters(), config.sourceView());
    }

    private DUUIDeserializer<JCas> processDeserializer(DUUICommunicationLayer communicationLayer, DUUIV1Config config) {
        return (cas, input) -> communicationLayer.deserialize(cas, input, config.targetView());
    }

    public record Documentation(
        String annotator_name,
        String version,
        String description,
        String implementation_lang,
        Map<String, Object> meta,
        Map<String, Object> parameters
    ) {
    }
}
```

```java
package duui.pipeline.v1;

import org.apache.uima.jcas.JCas;

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
        if (sourceView == null) {
            sourceView = "_InitialView";
        }
        if (targetView == null) {
            targetView = "_InitialView";
        }
        if (parameters == null) {
            throw new IllegalArgumentException("parameters must not be null");
        }
    }
}

```

```yaml
duui-pipeline:

  DUUIDescription:
    - data-only structures

    - DUUIEvent:
    - DUUILog:
    - DUUIMetric:

    - DUUIAddress:
      - schema, namespace, address, token



    - DUUITimeline:
      - DUUI



    - DispatchMode: enum describing the compute domain of an operation
      CPU: cpu bound
      IO: i/o bound
      MIXED: mixed

    - DUUILifecycle: enum of lifecycle primitives underlying all phases
      CREATION:
      INACTIVE:
      ACTIVE:
      TERMINAL:

    - DUUIStatus: enum of stateful operations
      CREATION:
        DUUIResource:
          DUUISubject:

            DUUIArtifact:

            DUUIArtifact:

          DUUIService:

            DUUIAdapter:

      INACTIVE:
      ACTIVE:
      TERMINAL:


    - DUUIPhase: hierarchical anchor for a single DUUIStatus. the idea is certain methods like process, analyse, serialize, etc. represents phases with a corresponding DUUIStatus. Every DUUIEntity is assigned a DUUIPhase every time it enters a phaseful method which triggers a DUUIEvent on entry and exit, and all logs and metrics gathered within the scope of that phase are assigned to it, unless a phaseful method is called within that method in which case that subphase is assigned as a child phase and the log and metric anchoring is scoped to that child phase.
      fields:
        - GID id -> ULID
        - DUUIStatus phase


        - Set<DUUIPhase> forks
        - Set<DUUILog> logs
        - Set<DUUIMetric> metrics
        - Set<DUUIEntity> entities
        -


      methods:
        -


    - \@Phase: annotation placed above phaseful methods to trigger an aspect wrapping function to handle the phase anchoring
      DUUIStatus status:
      DispatchMode mode:

    - DUUIFileMetadata:
    - DUUIDocumentMetadata:
    - DUUIDirectoryMetadata:


  DUUIEntity (has a timeline) :
    DUUIResource:

      DUUIService:

      DUUISubject:

        DUUIFile:

          DUUIDocument:

          DUUIDirectory:

        DUUIArtifact<A>:
          - metadata
          - subject -> duuidocument?
          -

        DUUIV1Artifact: DUUIArtifact<JCas>


    DUUIObject:

  DUUIClient:

    DUUIDocumentClient:
    DUUIStorageClient:
    DUUIVirtualizationClient:
    DUUIHostClient:

  DUUIService:

    DUUIDatabase:

    DUUICache:

    DUUIServer:
      - port/ports


    DUUIEndpoint:

      DUUIContainerRegistry:

      DUUIUimaNode:
        - AnalysisEngine engine;
        -

      DUUIV1Node:

      DUUIV2Node:

    DUUIProcess:
      - start
      - stop
      - kill
      - restart
      - pause > P
      - unpause > P

    DUUIContainerImage:
      - build
        - name
      - pull
        - tag
      - push
        - tag

    DUUIContainer: DUUIProcess (and DUUIServer?)
      - start > run
      - ports? or instead it holds a DUUIEndpoint so something like endpoint(int port) returns a DUUIEndpoint
      -

    DUUICluster:


  DUUIPrimitive:

    DUUIStream<DUU>:
      - listene

    DUUIExplorer:
      - traverse a DUUIDirectory



  DUUISubject:
    DUUIFile:
      - supertype for documents and directory
      - metadata -> async operation

    DUUIDocument:
      - mediatype
      - file-data -> async stream

    DUUIDirectory:
      - metadata -> async callback
      - children -> async stream


  DUUIArtifact<A>:
    - artifact object
    - metadata
      - source-file format
    - transformation ops
  DUUIPipeline:
    DUUICheckpoint:
      Source:
        varient-1:
          DUUICollectionReader:
        variant-2:
          - DUUIDiscoverer
          - DUUIAdapter:
            - DUUIReader:
              - supported formats
              - deserialize into jcas
            - DUUIWriter:
              - supported formats
              - serialize jcas into transport
            - aggregate variants for multiple formats
              - DUUIMultiReader
              - DUUIMultiWriter

      Processor:

      Target:
```

```yaml

```
