package duui.async;

public final class DUUIJfrPhaseState {
    private boolean started;
    private boolean stopped;

    public synchronized void started() {
        started = true;
    }

    public synchronized boolean isStarted() {
        return started;
    }

    public synchronized void stopped() {
        stopped = true;
    }

    public synchronized boolean isStopped() {
        return stopped;
    }
}
