# TaxoNERD actual legacy baseline comparison

Generated from the actual running legacy endpoint `http://127.0.0.1:9715` and the running generated MsgPack endpoint `http://127.0.0.1:9716` on 2026-05-26.

Baseline definition: `legacy-taxonerd-whole-document` is the old DUUI TaxoNERD JSON/Lua endpoint. It does not use generated MsgPack/Lua or async greedy response handling.

## Current 2-XMI Run

Documents: `4513701.xmi.gz`, `4566707.xmi.gz`. Total input: 20,537 chars, 892 sentences, 8,978 tokens, 314 named entities.

| variant | docs | elapsed ms per doc | median ms | speedup vs legacy | found | linked | failed | ANN ms | exact ms | cache hits/misses |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `legacy-taxonerd-whole-document` | 2 | 1013 / 695 | 1013 | 1.000x | 220 | 220 | 0 | 0.0 | 0.000 | 0/0 |
| `async-taxonerd-legacy-procedure-gbif` | 2 | 802 / 1925 | 1925 | 0.526x | 220 | 220 | 0 | 0.0 | 0.000 | 0/0 |
| `async-taxonerd-whole-document-gbif` | 2 | 7558 / 1111 | 7558 | 0.134x | 218 | 218 | 0 | 80.9 | 5.034 | 0/291 |
| `async-taxonerd-whole-document-gbif-linker-original` | 2 | 756 / 1035 | 1035 | 0.979x | 218 | 218 | 0 | 47.5 | 4.497 | 0/291 |
| `async-taxonerd-whole-document-gbif-linker-batched` | 2 | 995 / 1540 | 1540 | 0.658x | 218 | 218 | 0 | 56.3 | 4.629 | 0/291 |
| `async-taxonerd-whole-document-gbif-linker-cached` | 2 | 731 / 1083 | 1083 | 0.935x | 218 | 218 | 0 | 0.0 | 5.443 | 291/0 |
| `async-taxonerd-legacy-compatible-gbif-linker-original-ef200` | 2 | 772 / 2267 | 2267 | 0.447x | 220 | 220 | 0 | 748.2 | 0.003 | 0/376 |
| `async-taxonerd-legacy-compatible-gbif-linker-batched-ef200` | 2 | 747 / 1098 | 1098 | 0.923x | 220 | 220 | 0 | 81.7 | 0.004 | 0/376 |
| `async-taxonerd-legacy-compatible-gbif-linker-cached-ef200` | 2 | 743 / 1127 | 1127 | 0.899x | 220 | 220 | 0 | 69.1 | 0.003 | 0/376 |
| `async-taxonerd-span-sentence-gbif` | 2 | 871 / 1187 | 1187 | 0.853x | 258 | 258 | 0 | 21.0 | 6.004 | 113/55 |
| `async-taxonerd-span-paragraph-gbif` | 2 | 729 / 1141 | 1141 | 0.888x | 222 | 222 | 0 | 14.2 | 5.763 | 270/17 |
| `async-taxonerd-span-div-gbif` | 2 | 1453 / 1902 | 1902 | 0.533x | 275 | 275 | 0 | 358.3 | 9.230 | 347/32 |
| `async-taxonerd-span-section-gbif` | 2 | 518 / 897 | 897 | 1.129x | 0 | 0 | 2 | 0.0 | 0.000 | 0/0 |
| `async-taxonerd-span-title-gbif` | 2 | 500 / 1367 | 1367 | 0.741x | 0 | 0 | 2 | 0.0 | 0.000 | 0/0 |

Note: the Java report uses upper median for even-sized groups. The true two-value median for legacy is 854.0 ms; the report median is 1013 ms.

## Fuseki ANN Result

Partial measured Fuseki run was stopped after the first completed XMI because it blocked the single msgpack worker. First doc result: `4513701.xmi.gz` elapsed `61394` ms, found/linked `13/13`. Actual legacy on the same document found/linked `72/72` in `1013` ms in the current run.

This is not a competitive optimization path in its current form: it is slower by roughly 60x on that document and changes output semantics catastrophically.

## Older 45-XMI Context

The older broad run in `taxonerd_big_evaluation_report.md` used 45 XMI/GZip documents and the same actual legacy baseline.

| variant | docs | median ms | p95 ms | found | linked | conclusion |
|---|---:|---:|---:|---:|---:|---|
| `legacy-taxonerd-whole-document` | 45 | 608 | 1216 | 916 | 916 | actual baseline |
| `async-taxonerd-whole-document-gbif` | 45 | 592 | 1484 | 914 | 914 | only 1.027x median speedup, slower on large docs |
| `async-taxonerd-span-sentence-gbif` | 45 | 938 | 1569 | 957 | 957 | slower and changed output |
| `async-taxonerd-span-paragraph-gbif` | 45 | 1586 | 2929 | 935 | 935 | slower and changed output |

## Bottom Line

Actual legacy remains the baseline to beat. On the current XMI pair, the best correct-parity async variant is `async-taxonerd-legacy-compatible-gbif-linker-batched-ef200`: 747/1098 ms per doc, 220/220 found and linked, but still below the report-median legacy speed (`0.923x`).

The major confirmed optimization is batched ANN versus original ANN inside the legacy-compatible path: original EF200 spent 748.2 ms in ANN; batched EF200 spent 81.7 ms for identical 220/220 output. That fixes linker overhead, but end-to-end still does not decisively beat actual legacy.

Span variants are not valid speed wins here: sentence/div inflate matches, section/title produce zero output and fail, paragraph is close on latency but not identical in found count on the current run and was much slower in the 45-document run.
