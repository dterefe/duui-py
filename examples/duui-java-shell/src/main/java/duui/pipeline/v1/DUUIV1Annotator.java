package duui.pipeline.v1;

import com.fasterxml.jackson.databind.ObjectMapper;
import duui.clients.http.DUUIChannel;
import duui.clients.http.DUUIDeserializer;
import duui.clients.http.DUUIHttpMethod;
import duui.clients.http.DUUISignal;
import duui.communication.DUUICommunicationLayer;
import duui.communication.DUUILuaCommunicationLayer;
import duui.ems.DUUIActor;
import duui.ems.DUUIArtifact;
import org.apache.uima.UIMAFramework;
import org.apache.uima.cas.CASException;
import org.apache.uima.jcas.JCas;
import org.apache.uima.resource.metadata.TypeSystemDescription;
import org.apache.uima.util.XMLInputSource;

import duui.clients.http.DUUISerializer;
import duui.clients.http.IDUUIEndpoint;

import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.Objects;

public final class DUUIV1Annotator extends DUUIActor {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    @FunctionalInterface
    public interface Processor {
        void process(JCas cas) throws Exception;
    }

    private final IDUUIEndpoint endpointHandle;
    private final DUUIV1Config config;
    private final Documentation documentation;
    private final TypeSystemDescription typesystem;
    private final DUUICommunicationLayer communicationLayer;
    private final Processor processor;
    private final DUUISignal<Documentation> documentationSignal;
    private final DUUISignal<TypeSystemDescription> typesystemSignal;
    private final DUUISignal<DUUICommunicationLayer> communicationLayerSignal;
    private final DUUIChannel<JCas> processChannel;

    public DUUIV1Annotator(String id, IDUUIEndpoint endpoint, DUUIV1Config config) throws Exception {
        super(id);
        this.endpointHandle = Objects.requireNonNull(endpoint, "endpoint");
        this.config = Objects.requireNonNull(config, "config");
        this.documentationSignal = documentationSignal(endpoint);
        this.typesystemSignal = typesystemSignal(endpoint);
        this.communicationLayerSignal = communicationLayerSignal(endpoint);
        this.documentation = documentationSignal.request();
        this.typesystem = typesystemSignal.request();
        this.communicationLayer = communicationLayerSignal.request();
        this.processChannel = processChannel(endpoint, communicationLayer, config);
        this.processor = cas -> processChannel.request(cas);
    }

    public DUUIV1Annotator(
        String id,
        IDUUIEndpoint endpoint,
        DUUIV1Config config,
        Documentation documentation,
        TypeSystemDescription typesystem,
        DUUICommunicationLayer communicationLayer,
        Processor processor
    ) {
        super(id);
        this.endpointHandle = Objects.requireNonNull(endpoint, "endpoint");
        this.config = Objects.requireNonNull(config, "config");
        this.documentation = Objects.requireNonNull(documentation, "documentation");
        this.typesystem = Objects.requireNonNull(typesystem, "typesystem");
        this.communicationLayer = Objects.requireNonNull(communicationLayer, "communicationLayer");
        this.processor = Objects.requireNonNull(processor, "processor");
        this.documentationSignal = documentationSignal(endpoint);
        this.typesystemSignal = typesystemSignal(endpoint);
        this.communicationLayerSignal = communicationLayerSignal(endpoint);
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

    public void serialize(JCas cas, OutputStream stream, Map<String, String> parameters, String sourceView) throws CASException {
        communicationLayer.serialize(cas, stream, parameters, sourceView);
    }

    public void deserialize(JCas cas, InputStream stream, String targetView) throws CASException {
        communicationLayer.deserialize(cas, stream, targetView);
    }

    public void process(DUUIArtifact<JCas> artifact) throws Exception {
        artifact.record("PROCESS", id());
        processor.process(artifact.value());
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
        DUUISerializer<JCas> serializer = processSerializer(communicationLayer, config);
        DUUIChannel.ResponseApplier<JCas> applier = processDeserializer(communicationLayer, config);
        return new DUUIChannel<>(endpoint, DUUIHttpMethod.POST, "/v1/process", serializer, applier);
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

    private DUUIChannel.ResponseApplier<JCas> processDeserializer(DUUICommunicationLayer communicationLayer, DUUIV1Config config) {
        return (cas, input) -> {
            communicationLayer.deserialize(cas, input, config.targetView());
            return cas;
        };
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
