package duui.ems;

import java.util.concurrent.atomic.AtomicReference;

public class DUUISubject<T> extends DUUIEntity {
    private final AtomicReference<T> value;

    public DUUISubject(String id, T value) {
        super(id);
        this.value = new AtomicReference<>(value);
    }

    public T value() {
        return value.get();
    }

    public void value(T value) {
        this.value.set(value);
    }
}
