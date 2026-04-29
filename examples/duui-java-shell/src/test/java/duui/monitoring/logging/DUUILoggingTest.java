package duui.monitoring.logging;

import duui.TestComposerSupport;
import duui.monitoring.model.DUUILogLevel;
import duui.monitoring.model.DUUIScope;
import duui.monitoring.model.DUUILog;
import org.junit.jupiter.api.Test;

import java.util.Map;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DUUILoggingTest {
    @Test
    void loggerEmitsStructuredEvent() {
        DUUIInMemoryEventEmitter emitter = new DUUIInMemoryEventEmitter();
        DUUILogger logger = new DUUILogger(emitter, "test");

        logger.info("hello");

        assertEquals(1, emitter.events().size());
        DUUILog event = (DUUILog) emitter.events().getFirst();
        assertEquals(DUUILogLevel.INFO, event.level());
    }

    @Test
    void julHandlerUsesActiveScope() {
        TestComposerSupport.composer();
        DUUIInMemoryEventEmitter emitter = new DUUIInMemoryEventEmitter();
        DUUIJulHandlerLogger handler = new DUUIJulHandlerLogger(emitter);
        Logger logger = Logger.getLogger("dep");
        logger.addHandler(handler);
        logger.setUseParentHandlers(false);

        DUUILogContext.push(new DUUIScope("scope-1", "phase", null, Map.of("phase", "x")));
        try {
            logger.info("from-jul");
        } finally {
            DUUILogContext.pop();
            logger.removeHandler(handler);
        }

        DUUILog event = (DUUILog) emitter.events().getFirst();
        assertEquals("scope-1", event.scope().id());
        assertEquals("from-jul", event.message());
    }
}
