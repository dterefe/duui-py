# DUUI Java Shell (Minimal)

Minimal Java 21 shell for testing local `duui-py` annotators without orchestration.

## Package layout

- `duui.communication`
- `duui.pipeline` and `duui.pipeline.v1`
- `duui.clients`, `duui.clients.http`, `duui.clients.hosts`, `duui.clients.documents`
- `duui.handle`
- `duui.hosts`, `duui.hosts.os`, `duui.hosts.virtualization`
- `duui.ems`, `duui.ems.traits`
- `duui.monitoring.events`, `duui.monitoring.telemetry`
- `duui.adapters`

## V1 shell core

- `DUUIProxy` + `DUUIAddress` (`DUUIPath`, `DUUIUri`)
- `DUUIV1Protocol` with default `instantiate()` bootstrap
- `DUUIEndpoint` as concrete protocol handle with channel pool
- `DUUILease<DUUIChannel>` generic lease abstraction
- `DUUIChannel` as one HTTP channel + copied comm layer + one `DUUIPipe`
- `DUUIPipe` replayable input stream composed of two `DUUISignal` pairs:
  - request signal for `serialize -> analyse`
  - response signal for `analyse -> deserialize`

## Build

```bash
mvn -f examples/duui-java-shell/pom.xml -DskipTests package
```

## Run

```bash
mvn -f examples/duui-java-shell/pom.xml -DskipTests exec:java \
  -Dexec.args="--endpoint=http://localhost:9714 --text='hello from java shell' --lang=en --channels=1"
```
