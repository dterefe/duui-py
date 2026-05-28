# Corrected TaxoNERD GBIF Baseline vs Async Evaluation

This report replaces the rejected TaxoNERD result that compared different package-path and preload states. It uses the DUUI rework runtime and XMI documents only.

- Samples: 8 XMI documents
- Baseline: buffered HTTP POST, `streamingTransport(false)`
- Async variant: streaming HTTP POST, `streamingTransport(true)`
- Measurement hygiene: both containers freshly restarted, then warmed symmetrically before measured rows
- Async image state: `PYTHONPATH=/app/src`, `TAXONERD_PRELOAD=false`
- Numeric metric fields: complete
- Target taxon count equality: 8/8 rows

Baseline total latency: 627,396 ms.

Async total latency: 617,952 ms.

Total speedup: 1.015x.

| document | chars | baseline ms | async ms | speedup | baseline wait ms | async request ms | baseline response bytes | async response bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 14837245 | 5410 | 18708 | 18478 | 1.01x | 18670 | 18430 | 1506 | 1235 |
| 4655058 | 22461 | 254698 | 254718 | 1.00x | 254663 | 254688 | 9623 | 6313 |
| 3735223 | 19055 | 51928 | 50116 | 1.04x | 51899 | 50097 | 1507 | 1226 |
| 4656657 | 16736 | 42581 | 44178 | 0.96x | 42546 | 44152 | 2793 | 1871 |
| 12671649 | 22141 | 38748 | 37636 | 1.03x | 38726 | 37615 | 592 | 642 |
| 13776082 | 17560 | 28628 | 28383 | 1.01x | 28609 | 28359 | 1586 | 1244 |
| 4543820 | 12401 | 46975 | 45669 | 1.03x | 46957 | 45646 | 836 | 840 |
| 3713536 | 7880 | 145130 | 138774 | 1.05x | 145104 | 138754 | 22389 | 14798 |

The corrected result is process/linker-bound. Transport changes reduce the response payload, but they do not materially change total TaxoNERD GBIF latency for this steady-state configuration.
