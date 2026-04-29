package duui.async;

import java.util.UUID;

final class DUUIUlids {
    String next() {
        return UUID.randomUUID().toString();
    }
}
