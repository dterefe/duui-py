# Corrected TaxoNERD GBIF Baseline vs Async Summary

Source matrix: `/home/stud_homes/s0424382/projects/ttlab/duui-alpha/duui-py/reports/latest-evaluation-20260527-122624/exact-baseline-vs-async-rework-only/matrix.tsv`

Run properties:

- Annotator: TaxoNERD with GBIF linking.
- Runtime path: DUUI rework runtime only.
- Baseline: buffered HTTP POST with `streamingTransport(false)`.
- Async variant: streaming transport with `streamingTransport(true)`.
- Samples: 8 XMI documents, 5410-22461 characters.
- Measurement hygiene: both TaxoNERD containers were freshly restarted and the existing symmetric warmup switch was enabled before measured rows.
- Async image: `PYTHONPATH=/app/src`, `TAXONERD_PRELOAD=false`; the vendored TaxoNERD package path is not active.
- Completeness: `metricRequired(...)` was used for every reported metric; missing numeric metrics = 0.
- Correctness check: `output_equal=true` for 8/8 rows by target taxon count.

| metric | value |
|---|---:|
| baseline total latency | 627,396 ms |
| async total latency | 617,952 ms |
| total speedup | 1.015x |
| median per-document speedup | 1.021x |
| baseline median latency | 44,778.0 ms |
| async median latency | 44,923.5 ms |
| baseline p95 latency | 216,349.2 ms |
| async p95 latency | 214,137.6 ms |
| baseline request bytes | 126,776 |
| async request bytes | 128,713 |
| baseline response bytes | 40,832 |
| async response bytes | 28,169 |

The corrected TaxoNERD result does not support the previous large-speedup claim. With package path and preload asymmetry removed and both services warmed symmetrically, total latency is essentially process/linker-bound: the async variant is 1.015x overall. The response payload is smaller, but transport is not the dominant cost for this TaxoNERD GBIF configuration.
