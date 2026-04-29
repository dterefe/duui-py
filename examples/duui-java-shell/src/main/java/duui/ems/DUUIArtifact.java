package duui.ems;

import java.time.Instant;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

public final class DUUIArtifact<T> extends DUUISubject<T> {
    private final CopyOnWriteArrayList<HistoryEntry> history = new CopyOnWriteArrayList<>();

    public DUUIArtifact(String id, T value) {
        super(id, value);
    }

    public void record(String phase, String detail) {
        history.add(new HistoryEntry(Instant.now(), phase, detail));
    }

    public List<HistoryEntry> history() {
        return List.copyOf(history);
    }

    public record HistoryEntry(Instant timestamp, String phase, String detail) {
    }
}
