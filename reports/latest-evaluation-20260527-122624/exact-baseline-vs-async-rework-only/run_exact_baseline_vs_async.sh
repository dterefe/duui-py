#!/usr/bin/env bash
set -uo pipefail
ROOT=/home/stud_homes/s0424382/projects/ttlab/duui-alpha
RUN_DIR="$ROOT/duui-py/reports/latest-evaluation-20260527-122624/exact-baseline-vs-async-rework-only"
cd "$ROOT/DockerUnifiedUIMAInterface"
SAMPLES=$(paste -sd, "$RUN_DIR/sample_files.txt")
rm -f "$RUN_DIR/matrix.tsv" \
  "$RUN_DIR/exact_numeric_rows.csv" \
  "$RUN_DIR/exact_summary.csv" \
  "$RUN_DIR/exact_summary.md"
run_one() {
  local name="$1" method="$2"; shift 2
  local report_dir="$RUN_DIR/surefire-${name}-all-scales"
  rm -rf "$report_dir"
  mkdir -p "$report_dir"
  printf '===== %s all-scales =====\n' "$name" | tee "$RUN_DIR/${name}.status"
  local start end rc
  start=$(date +%s)
  set -o pipefail
  mvn -Dmaven.test.skip=false -DskipTests=false -DfailIfNoTests=false -Dsurefire.useFile=false -Dsurefire.reportsDirectory="$report_dir" \
    -Dtest=DUUILegacyModernAnnotatorMatrixTest#$method \
    -Dduui.py.matrix.report="$RUN_DIR/matrix.tsv" -Dduui.py.matrix.repeats=1 \
    -Dduui.py.matrix.warmup=true \
    -Dduui.py.spacy.repeats=1 \
    -Dduui.py.spacy.model_size=sm \
    -Dduui.py.spacy.legacy.endpoint=http://127.0.0.1:19729 \
    -Dduui.py.spacy.endpoint=http://127.0.0.1:19719 \
    -Dduui.py.taxonerd.legacy.endpoint=http://127.0.0.1:19818 \
    -Dduui.py.taxonerd.msgpack.endpoint=http://127.0.0.1:19819 \
    -Dduui.py.taxonerd.model=en_ner_eco_md \
    -Dduui.py.taxonerd.linking=gbif_backbone \
    -Dduui.py.taxonerd.input_strategy=legacy-procedure \
    -Dduui.py.taxonerd.linker_strategy=ann-original \
    -Dduui.py.gazetteer.legacy.endpoint=http://127.0.0.1:19828 \
    -Dduui.py.gazetteer.msgpack.endpoint=http://127.0.0.1:19829 \
    -Dduui.py.gnfinder.legacy.endpoint=http://127.0.0.1:19838 \
    -Dduui.py.gnfinder.msgpack.endpoint=http://127.0.0.1:19839 \
    -Dduui.py.spacy.sample.files="$SAMPLES" \
    -Dduui.py.taxonerd.sample.files="$SAMPLES" \
    -Dduui.py.gazetteer.sample.files="$SAMPLES" \
    -Dduui.py.gnfinder.sample.files="$SAMPLES" \
    test 2>&1 | tee "$RUN_DIR/${name}.log"
  rc=${PIPESTATUS[0]}
  end=$(date +%s)
  printf 'exit_code=%s elapsed_s=%s samples=%s\n' "$rc" "$((end-start))" "$(wc -l < "$RUN_DIR/sample_files.txt")" | tee -a "$RUN_DIR/${name}.status"
  return "$rc"
}
failed=0
run_one spacy compareSpacyLegacyCustomLuaAndModernGeneratedMsgpackLuaOnXmi || failed=1
run_one taxonerd compareTaxonerdLegacyJsonLuaAndModernGeneratedMsgpackLuaOnXmi || failed=1
run_one gazetteer compareGazetteerLegacyJsonLuaAndModernGeneratedMsgpackLuaOnXmi || failed=1
run_one gnfinder compareGNFinderLegacyXmiLuaAndModernGeneratedMsgpackLuaOnXmi || failed=1
exit "$failed"
