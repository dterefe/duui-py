package duui.clients.documents;

import duui.clients.handle.DUUIAddress;
import duui.clients.handle.DUUIProxy;

import java.time.Instant;

public abstract class DUUIDirectory implements DUUIProxy {
    private final DUUIAddress address;
    private final String name;
    private final Instant createdAt;
    private final Instant modifiedAt;
    private final Instant accessedAt;

    protected DUUIDirectory(
        DUUIAddress address,
        String name,
        Instant createdAt,
        Instant modifiedAt,
        Instant accessedAt
    ) {
        this.address = address;
        this.name = name;
        this.createdAt = createdAt;
        this.modifiedAt = modifiedAt;
        this.accessedAt = accessedAt;
    }

    @Override
    public final DUUIAddress address() {
        return address;
    }

    public final String name() {
        return name;
    }

    public final Instant createdAt() {
        return createdAt;
    }

    public final Instant modifiedAt() {
        return modifiedAt;
    }

    public final Instant accessedAt() {
        return accessedAt;
    }

    public abstract boolean exists() throws DUUIDocumentException;

    public abstract boolean readable() throws DUUIDocumentException;

    public abstract boolean writable() throws DUUIDocumentException;

    public abstract boolean hidden() throws DUUIDocumentException;

    public abstract DUUIFile file(String name) throws DUUIDocumentException;

    public abstract DUUIDirectory directory(String name) throws DUUIDocumentException;

    public abstract DUUIDirectory create() throws DUUIDocumentException;

    public abstract DUUIDirectory createDirectories() throws DUUIDocumentException;

    public abstract DUUIDirectory copyTo(DUUIDirectory target) throws DUUIDocumentException;

    public abstract DUUIDirectory moveTo(DUUIDirectory target) throws DUUIDocumentException;

    public abstract DUUIDirectory rename(String name) throws DUUIDocumentException;

    public abstract void delete() throws DUUIDocumentException;

    public abstract DUUIDirectory parent() throws DUUIDocumentException;
}
