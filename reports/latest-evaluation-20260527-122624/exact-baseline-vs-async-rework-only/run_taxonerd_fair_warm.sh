#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/stud_homes/s0424382/projects/ttlab/duui-alpha
RUN_DIR="$ROOT/duui-py/reports/latest-evaluation-20260527-122624/exact-baseline-vs-async-rework-only"
REPORT_DIR="$RUN_DIR/surefire-taxonerd-fair-warm-rerun"
SAMPLES=$(paste -sd, "$RUN_DIR/sample_files.txt")

rm -f "$RUN_DIR/matrix.tsv" \
  "$RUN_DIR/exact_numeric_rows.csv" \
  "$RUN_DIR/exact_summary.csv" \
  "$RUN_DIR/exact_summary.md" \
  "$RUN_DIR/taxonerd.log" \
  "$RUN_DIR/taxonerd.status"
rm -rf "$REPORT_DIR"
mkdir -p "$REPORT_DIR"

cd "$ROOT/DockerUnifiedUIMAInterface"
printf '===== taxonerd fair symmetric-warmup rerun =====\n' | tee "$RUN_DIR/taxonerd.status"
start=$(date +%s)
mvn -Dmaven.test.skip=false -DskipTests=false -DfailIfNoTests=false -Dsurefire.useFile=false -Dsurefire.reportsDirectory="$REPORT_DIR" \
  -Dtest=DUUILegacyModernAnnotatorMatrixTest#compareTaxonerdLegacyJsonLuaAndModernGeneratedMsgpackLuaOnXmi \
  -Dduui.py.matrix.report="$RUN_DIR/matrix.tsv" -Dduui.py.matrix.repeats=1 \
  -Dduui.py.matrix.warmup=true \
  -Dduui.py.taxonerd.legacy.endpoint=http://127.0.0.1:19818 \
  -Dduui.py.taxonerd.msgpack.endpoint=http://127.0.0.1:19819 \
  -Dduui.py.taxonerd.model=en_ner_eco_md \
  -Dduui.py.taxonerd.linking=gbif_backbone \
  -Dduui.py.taxonerd.input_strategy=legacy-procedure \
  -Dduui.py.taxonerd.linker_strategy=ann-original \
  -Dduui.py.taxonerd.sample.files="$SAMPLES" \
  test 2>&1 | tee "$RUN_DIR/taxonerd.log"
rc=${PIPESTATUS[0]}
end=$(date +%s)
printf 'exit_code=%s elapsed_s=%s samples=%s symmetric_warmup=true\n' "$rc" "$((end-start))" "$(wc -l < "$RUN_DIR/sample_files.txt")" | tee -a "$RUN_DIR/taxonerd.status"
exit "$rc"
