# TaxoNERD correctness evaluation

Baseline: `legacy-taxonerd-whole-document` is the actual legacy DUUI TaxoNERD endpoint using the old custom JSON/Lua communication path. It is not using the generated MsgPack/Lua runtime path or async greedy response handling.

| variant | docs | chars | input_sentences | input_tokens | input_ne | expected | found | linked | missing | failed | median_ms | linker_ann_ms | linker_exact_ms | cache_hits | cache_misses | fuseki_ms | fuseki_aliases | fuseki_matches | fuseki_errors | metric_events |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| async-taxonerd-legacy-compatible-gbif-fuseki-ann-cached-ef200 | 12 | 116643 | 1120 | 38867 | 747 | 0 | 68 | 68 | 0 | 0 | 691 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 144 |

## Missing mentions

