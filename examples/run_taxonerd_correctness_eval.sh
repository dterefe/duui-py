#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JAVA_ROOT="$(cd "$ROOT/DockerUnifiedUIMAInterface" && pwd)"
PY_ROOT="$ROOT/duui-py"

docker rm -f taxonerd-legacy taxonerd-msgpack taxonerd-span >/dev/null 2>&1 || true

docker run -d --name taxonerd-legacy -p 19718:9714 \
  -v "$PY_ROOT/src:/app/src:ro" \
  -v "$PY_ROOT/examples/taxonerd-legacy-lua:/app/examples/taxonerd-legacy-lua:ro" \
  duui-py-taxonerd-legacy:local >/dev/null
docker run -d --name taxonerd-msgpack -p 19719:9714 \
  -v "$PY_ROOT/src:/app/src:ro" \
  -v "$PY_ROOT/examples/taxonerd-msgpack-lua:/app/examples/taxonerd-msgpack-lua:ro" \
  duui-py-taxonerd-msgpack:local >/dev/null
docker run -d --name taxonerd-span -p 19720:9714 \
  -v "$PY_ROOT/src:/app/src:ro" \
  -v "$PY_ROOT/examples/taxonerd-msgpack-lua:/app/examples/taxonerd-msgpack-lua:ro" \
  --entrypoint uvicorn \
  duui-py-taxonerd-msgpack:local \
  taxonerd_span_window_annotator:app --host 0.0.0.0 --port 9714 >/dev/null

for port in 19718 19719 19720; do
  for _ in $(seq 1 120); do
    if curl -fsS "http://127.0.0.1:${port}/v1/documentation" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  curl -fsS "http://127.0.0.1:${port}/v1/documentation" >/dev/null
done

(
  cd "$JAVA_ROOT"
  mvn -q -Dmaven.test.skip=false -DskipTests=false -Dtest=org.texttechnologylab.duui.rework.DUUITaxonerdCorrectnessEvaluationTest test
)
