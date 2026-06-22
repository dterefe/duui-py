#!/usr/bin/env bash
set -euo pipefail

ROOT="${DUUI_ALPHA_ROOT:-/home/stud_homes/s0424382/projects/ttlab/duui-alpha}"
DUUI="${ROOT}/DockerUnifiedUIMAInterface"
OUT_ROOT="${DUUI_EVAL_OUT:-/storage/projects/BIOfid/code/dterefe/duui-py-eval-2026-06-01}"
RUN_ID="${DUUI_EVAL_RUN_ID:-$(date -u +%Y%m%d-%H%M%S)}"
OUT="${OUT_ROOT}/parameter-dua-artifacts-${RUN_ID}"

PARAM_OUTPUT="${OUT}/duui-py-parameter-sweep.tsv"
DUA_OUTPUT="${OUT}/dua-cas-vs-backends"

DOCUMENTS="${DUUI_EVAL_DOCUMENTS:-25}"
WARMUP_DOCUMENTS="${DUUI_EVAL_WARMUP_DOCUMENTS:-3}"
LATENCY_SAMPLES="${DUUI_EVAL_LATENCY_SAMPLES:-5}"
TEXT_REPEATS="${DUUI_EVAL_TEXT_REPEATS:-1}"
REQUEST_TIMEOUT_SECONDS="${DUUI_EVAL_REQUEST_TIMEOUT_SECONDS:-900}"

DUA_DOCUMENTS="${DUA_EVAL_DOCUMENTS:-200}"
DUA_OPERATIONS="${DUA_EVAL_OPERATIONS:-400}"
DUA_WORKLOADS="${DUA_EVAL_WORKLOADS:-read-heavy,balanced,ingest-heavy,graph-heavy,spatial-heavy}"

mkdir -p "${OUT}"

cat > "${OUT}/README.md" <<EOF
# DUUI-Py Parameter Optimization and CAS-vs-DUA Artifact Evaluation

Run id: ${RUN_ID}

This run has two phases:
1. DUUI-core remote V1 parameter sweep over the endpoints supplied in \`DUUI_PY_EVAL_ENDPOINTS\`.
2. DUA CAS/LMDB/PostgreSQL artifact evaluation through \`dua-benchmarks full-evaluation\`.

Only performance-relevant annotator parameters should be swept here. Deployment-only defaults
such as container internal port 9714 are intentionally outside the descriptor/evaluation surface.
EOF

echo "Output: ${OUT}"

echo "Building DUUI-core evaluator..."
(cd "${DUUI}" && mvn -q -pl duui-core -am -DskipTests compile)
(cd "${DUUI}" && mvn -q -pl duui-core dependency:build-classpath -Dmdep.outputFile=target/duui-core-eval.classpath)

echo "Building DUA benchmark artifact..."
(cd "${DUUI}" && mvn -q -pl duui-dua/dua-benchmarks -am package -DskipTests)

if [[ -n "${DUUI_PY_EVAL_ENDPOINTS:-}" ]]; then
  echo "Validating DUUI-Py endpoints..."
  IFS=',' read -ra endpoint_entries <<< "${DUUI_PY_EVAL_ENDPOINTS}"
  for entry in "${endpoint_entries[@]}"; do
    name="${entry%%=*}"
    url="${entry#*=}"
    if [[ -z "${name}" || -z "${url}" || "${name}" == "${url}" ]]; then
      echo "Invalid endpoint entry: ${entry}" >&2
      exit 2
    fi
    curl -fsS "${url%/}/v1/details/input_output" > "${OUT}/${name}-input-output.json"
    python3 - "$OUT/${name}-input-output.json" <<'PY'
import json
import sys
path = sys.argv[1]
data = json.load(open(path))
params = data.get("parameters")
if not isinstance(params, dict) or not params:
    raise SystemExit(f"{path}: missing descriptor parameters")
print(f"{path}: descriptor parameters={len(params)}")
PY
  done

  echo "Running parameter sweep through DUUI-core..."
  DUUI_CORE_CP="$(cat "${DUUI}/target/duui-core-eval.classpath")"
  (cd "${DUUI}" && java \
    -Dduui.py.eval.endpoints="${DUUI_PY_EVAL_ENDPOINTS}" \
    -Dduui.py.eval.parameters="${DUUI_PY_EVAL_PARAMETERS:-}" \
    -Dduui.py.eval.parameterVariants="${DUUI_PY_EVAL_PARAMETER_VARIANTS:-}" \
    -Dduui.py.eval.compareTypes="${DUUI_PY_EVAL_COMPARE_TYPES:-}" \
    -Dduui.py.eval.documents="${DOCUMENTS}" \
    -Dduui.py.eval.warmupDocuments="${WARMUP_DOCUMENTS}" \
    -Dduui.py.eval.latencySamples="${LATENCY_SAMPLES}" \
    -Dduui.py.eval.textRepeats="${TEXT_REPEATS}" \
    -Dduui.py.eval.requestTimeoutSeconds="${REQUEST_TIMEOUT_SECONDS}" \
    -Dduui.py.eval.output="${PARAM_OUTPUT}" \
    -cp "duui-core/target/classes:duui-base/target/classes:duui-storage/target/classes:${DUUI_CORE_CP}" \
    org.texttechnologylab.duui.core.evaluation.DUUIPyAnnotatorEvaluationMain)
else
  echo "DUUI_PY_EVAL_ENDPOINTS is empty; parameter sweep build validation completed but runtime sweep skipped." | tee "${OUT}/parameter-sweep-skipped.txt"
fi

echo "Running DUA CAS-vs-backend artifact evaluation..."
java --add-opens java.base/java.nio=ALL-UNNAMED \
  --add-exports java.base/sun.nio.ch=ALL-UNNAMED \
  -jar "${DUUI}/duui-dua/dua-benchmarks/target/dua-benchmarks.jar" \
  full-evaluation \
  --documents "${DUA_DOCUMENTS}" \
  --operations "${DUA_OPERATIONS}" \
  --workload "${DUA_WORKLOADS}" \
  --output "${DUA_OUTPUT}"

echo "Parameter/DUA evaluation complete: ${OUT}"
