package duui.clients.documents;

import duui.clients.handle.DUUIAddress;
import duui.clients.handle.DUUIProxy;
import jakarta.ws.rs.core.MediaType;

import java.io.InputStream;
import java.io.OutputStream;
import java.time.Instant;

public abstract class DUUIFile implements DUUIProxy {
    private final DUUIAddress address;
    private final String name;
    private final MediaType mediaType;
    private final long size;
    private final Instant createdAt;
    private final Instant modifiedAt;
    private final Instant accessedAt;

    protected DUUIFile(
        DUUIAddress address,
        String name,
        MediaType mediaType,
        long size,
        Instant createdAt,
        Instant modifiedAt,
        Instant accessedAt
    ) {
        this.address = address;
        this.name = name;
        this.mediaType = mediaType;
        this.size = size;
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

    public final MediaType mediaType() {
        return mediaType;
    }

    public final long size() {
        return size;
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

    public abstract InputStream read() throws DUUIDocumentException;

    public abstract byte[] readBytes() throws DUUIDocumentException;

    public abstract void downloadTo(OutputStream output) throws DUUIDocumentException;

    public abstract void write(InputStream input) throws DUUIDocumentException;

    public abstract void writeBytes(byte[] bytes) throws DUUIDocumentException;

    public abstract DUUIFile copyTo(DUUIDirectory target) throws DUUIDocumentException;

    public abstract DUUIFile moveTo(DUUIDirectory target) throws DUUIDocumentException;

    public abstract DUUIFile rename(String name) throws DUUIDocumentException;

    public abstract void delete() throws DUUIDocumentException;

    public abstract DUUIDirectory parent() throws DUUIDocumentException;
}
