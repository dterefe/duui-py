package duui.shell;

import duui.clients.http.DUUIHttpClient;
import duui.clients.http.IDUUIEndpoint;
import duui.ems.DUUIArtifact;
import duui.pipeline.DUUIComponent;
import duui.pipeline.DUUIMonoStage;
import duui.pipeline.DUUIPipeline;
import duui.pipeline.DUUIProcessorCheckpoint;
import duui.pipeline.DUUISourceCheckpoint;
import duui.pipeline.DUUITargetCheckpoint;
import duui.pipeline.v1.DUUIV1Annotator;
import duui.pipeline.v1.DUUIV1Config;
import duui.runtime.DUUIComposer;
import duui.scheduler.DUUIDirector;
import duui.scheduler.DUUIGovernor;
import duui.scheduler.DUUIScheduler;
import duui.scheduler.DUUISchedulerPolicy;
import org.apache.uima.fit.factory.JCasFactory;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.cas.ByteArrayFS;
import org.apache.uima.jcas.JCas;
import org.apache.uima.jcas.tcas.Annotation;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

public final class DuuiPyShellMain {
    public static void main(String[] args) throws Exception {
        Config config = Config.fromArgs(args);

        DUUIHttpClient.Descriptor descriptor = new DUUIHttpClient.Descriptor(
            config.endpointBase,
            10,
            config.timeoutSeconds,
            config.channels,
            config.requestPipeBufferBytes,
            config.responsePipeBufferBytes,
            config.initialReplayCapacityBytes
        );

        IDUUIEndpoint endpoint = new DUUIHttpClient().endpoint(descriptor);
        DUUIV1Annotator annotator = new DUUIV1Annotator(
            "annotator-0",
            endpoint,
            new DUUIV1Config(config.channels, "_InitialView", "_InitialView", config.parameters)
        );
        DUUIComponent component = new DUUIComponent("component-0", java.util.List.of(annotator));
        DUUIMonoStage stage = new DUUIMonoStage("stage-0", component);
        DUUISourceCheckpoint sourceCheckpoint = new DUUISourceCheckpoint("source", stage);
        DUUIProcessorCheckpoint processorCheckpoint = new DUUIProcessorCheckpoint("processor-0", stage);
        DUUITargetCheckpoint targetCheckpoint = new DUUITargetCheckpoint("target");
        DUUIPipeline pipeline = new DUUIPipeline()
            .add(sourceCheckpoint)
            .add(processorCheckpoint)
            .add(targetCheckpoint);
        DUUIComposer composer = new DUUIComposer(pipeline);
        DUUIDirector director = new DUUIDirector(DUUISchedulerPolicy.standard());
        DUUIScheduler scheduler = new DUUIScheduler(composer.pipeline());

        JCas source = JCasFactory.createJCas();
        source.setDocumentLanguage(config.language);
        if (config.audioFile != null && !config.audioFile.isBlank()) {
            byte[] audioBytes = Files.readAllBytes(Path.of(config.audioFile));
            ByteArrayFS sofaArray = source.getCas().createByteArrayFS(audioBytes.length);
            for (int i = 0; i < audioBytes.length; i++) {
                sofaArray.set(i, audioBytes[i]);
            }
            source.getCas().setSofaDataArray(sofaArray, "application/octet-stream");
        } else {
            source.setDocumentText(config.text);
        }

        DUUIArtifact<JCas> artifact = new DUUIArtifact<>("artifact-0", source);
        sourceCheckpoint.offer(artifact);
        scheduler.markSourceDrained();

        try (DUUIGovernor<DUUIPipeline> governor = new DUUIGovernor<>(composer.pipeline())) {
            while (true) {
                DUUIScheduler.Step step = scheduler.next();
                if (step instanceof DUUIScheduler.IdleStep) {
                    continue;
                }
                if (step instanceof DUUIScheduler.CompleteStep) {
                    break;
                }
                governor.register(director.dispatch(step));
            }
        }

        JCas target = (JCas) targetCheckpoint.poll().orElseThrow().value();
        long annCount = JCasUtil.select(target, Annotation.class).size();
        System.out.println("DUUI shell request completed");
        System.out.println("Endpoint: " + config.endpointBase);
        System.out.println("Channels: " + config.channels);
        System.out.println("Document text: " + target.getDocumentText());
        System.out.println("Annotation count: " + annCount);
    }

    private static final class Config {
        final String endpointBase;
        final String text;
        final String language;
        final int timeoutSeconds;
        final int channels;
        final int requestPipeBufferBytes;
        final int responsePipeBufferBytes;
        final int initialReplayCapacityBytes;
        final String audioFile;
        final Map<String, String> parameters;

        private Config(
            String endpointBase,
            String text,
            String language,
            int timeoutSeconds,
            int channels,
            int requestPipeBufferBytes,
            int responsePipeBufferBytes,
            int initialReplayCapacityBytes,
            String audioFile,
            Map<String, String> parameters
        ) {
            this.endpointBase = endpointBase;
            this.text = text;
            this.language = language;
            this.timeoutSeconds = timeoutSeconds;
            this.channels = channels;
            this.requestPipeBufferBytes = requestPipeBufferBytes;
            this.responsePipeBufferBytes = responsePipeBufferBytes;
            this.initialReplayCapacityBytes = initialReplayCapacityBytes;
            this.audioFile = audioFile;
            this.parameters = parameters;
        }

        static Config fromArgs(String[] args) {
            String endpoint = "http://localhost:9714";
            String text = "DUUI Java shell smoke test.";
            String language = "en";
            int timeoutSeconds = 30;
            int channels = 1;
            int requestPipeBufferBytes = 64 * 1024;
            int responsePipeBufferBytes = 64 * 1024;
            int initialReplayCapacityBytes = 1024 * 1024;
            Map<String, String> parameters = new HashMap<>();
            String audioFile = null;

            for (String arg : args) {
                if (arg.startsWith("--endpoint=")) {
                    endpoint = arg.substring("--endpoint=".length());
                } else if (arg.startsWith("--text=")) {
                    text = arg.substring("--text=".length());
                } else if (arg.startsWith("--lang=")) {
                    language = arg.substring("--lang=".length());
                } else if (arg.startsWith("--timeout-seconds=")) {
                    timeoutSeconds = Integer.parseInt(arg.substring("--timeout-seconds=".length()));
                } else if (arg.startsWith("--channels=")) {
                    channels = Integer.parseInt(arg.substring("--channels=".length()));
                } else if (arg.startsWith("--request-pipe-buffer-bytes=")) {
                    requestPipeBufferBytes = Integer.parseInt(arg.substring("--request-pipe-buffer-bytes=".length()));
                } else if (arg.startsWith("--response-pipe-buffer-bytes=")) {
                    responsePipeBufferBytes = Integer.parseInt(arg.substring("--response-pipe-buffer-bytes=".length()));
                } else if (arg.startsWith("--initial-replay-capacity-bytes=")) {
                    initialReplayCapacityBytes = Integer.parseInt(arg.substring("--initial-replay-capacity-bytes=".length()));
                } else if (arg.startsWith("--param=")) {
                    String value = arg.substring("--param=".length());
                    int eq = value.indexOf('=');
                    if (eq > 0 && eq < value.length() - 1) {
                        parameters.put(value.substring(0, eq), value.substring(eq + 1));
                    }
                } else if (arg.startsWith("--audio-file=")) {
                    audioFile = arg.substring("--audio-file=".length());
                }
            }

            return new Config(
                endpoint,
                text,
                language,
                timeoutSeconds,
                channels,
                requestPipeBufferBytes,
                responsePipeBufferBytes,
                initialReplayCapacityBytes,
                audioFile,
                parameters
            );
        }
    }
}
