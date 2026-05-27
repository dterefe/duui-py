# TaxoNERD large XMI evaluation

Run date: 2026-05-26

## Scope

- Documents: 45 XMI/GZip files from `preprocessed_corpora_sample_1000`.
- Selection: stratified by actual SOFA text length, not compressed file size.
- Strata: 15 small docs, 15 middle docs, 15 large docs.
- Total input text: 854,555 characters.
- Total input CAS annotations observed: 10,602 sentences, 302,616 tokens, 7,682 named entities.
- Variants: 9.
- Total DUUI document runs: 405.
- Run status: complete, Maven status 0, failed result rows 0.
- Model/linker: `en_ner_eco_md` with `gbif_backbone`.

Both legacy and runtime containers only had `en_ner_eco_md` installed. No German TaxoNERD LIVB model was available in either container, so these numbers are a same-model transport/strategy comparison, not a German-model quality claim.

## Baseline

The baseline is `legacy-taxonerd-whole-document`: the old custom JSON/Lua whole-document TaxoNERD endpoint using the legacy DUUI communication path. It does not use the generated MsgPack/Lua runtime path or async chunked response handling.

## Overall latency

| variant | docs | median ms | mean ms | p95 ms | p99 ms | min ms | max ms | speedup vs legacy median | found | linked | failed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| legacy-taxonerd-whole-document | 45 | 608 | 742.2 | 1216 | 1686 | 511 | 1686 | 1.000x | 916 | 916 | 0 |
| async-taxonerd-whole-document-gbif | 45 | 592 | 776.5 | 1484 | 2116 | 441 | 2116 | 1.027x | 914 | 914 | 0 |
| async-taxonerd-span-sentence-gbif | 45 | 938 | 1017.1 | 1569 | 2061 | 328 | 2061 | 0.648x | 957 | 957 | 0 |
| async-taxonerd-span-sentence-nproc2-gbif | 45 | 2549 | 2711.1 | 3774 | 3859 | 1636 | 3859 | 0.239x | 957 | 957 | 0 |
| async-taxonerd-span-sentence-nproc4-gbif | 45 | 3448 | 3515.2 | 4221 | 4796 | 2905 | 4796 | 0.176x | 957 | 957 | 0 |
| async-taxonerd-span-sentence-merged-gbif | 45 | 1493 | 1471.6 | 1761 | 2085 | 970 | 2085 | 0.407x | 915 | 915 | 0 |
| async-taxonerd-span-paragraph-gbif | 45 | 1586 | 1744.1 | 2929 | 2971 | 1209 | 2971 | 0.383x | 935 | 935 | 0 |
| async-taxonerd-span-paragraph-nproc2-gbif | 45 | 2582 | 2793.3 | 4213 | 4442 | 2261 | 4442 | 0.235x | 935 | 935 | 0 |
| async-taxonerd-span-paragraph-nproc4-gbif | 45 | 3159 | 3255.5 | 3927 | 4370 | 2784 | 4370 | 0.192x | 935 | 935 | 0 |

## Latency by document size

| stratum | chars | legacy median | whole-doc median | sentence median | sentence nproc2 | sentence nproc4 | sentence merged | paragraph median | paragraph nproc2 | paragraph nproc4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| small | 1,954-3,598 | 532 | 494 | 745 | 2412 | 3451 | 1464 | 1486 | 2582 | 3087 |
| middle | 9,418-9,527 | 605 | 583 | 844 | 2559 | 3364 | 1520 | 1489 | 2516 | 3285 |
| large | 34,437-58,842 | 978 | 1140 | 1370 | 3165 | 3524 | 1496 | 2044 | 3383 | 3053 |

## Transport and process medians

| variant | request bytes | response bytes | HTTP serialize ms | response decode ms | request duration ms | request decode ms | TaxoNERD strategy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy-taxonerd-whole-document | 9,790 | 1,073 | 1 | 2 | 588 | 0.09 | n/a |
| async-taxonerd-whole-document-gbif | 91,424 | 994 | 5 | 129 | 370 | 6.89 | 125.30 |
| async-taxonerd-span-sentence-gbif | 91,493 | 1,020 | 3 | 284 | 530 | 11.37 | 246.70 |
| async-taxonerd-span-sentence-nproc2-gbif | 91,505 | 1,020 | 4 | 2010 | 2306 | 17.81 | 1985.97 |
| async-taxonerd-span-sentence-nproc4-gbif | 91,505 | 1,020 | 3 | 2744 | 3163 | 19.99 | 2720.45 |
| async-taxonerd-span-sentence-merged-gbif | 91,511 | 991 | 2 | 923 | 1253 | 16.05 | 905.80 |
| async-taxonerd-span-paragraph-gbif | 91,526 | 1,009 | 3 | 975 | 1270 | 15.54 | 957.74 |
| async-taxonerd-span-paragraph-nproc2-gbif | 91,538 | 1,009 | 3 | 2019 | 2303 | 17.44 | 1990.36 |
| async-taxonerd-span-paragraph-nproc4-gbif | 91,538 | 1,009 | 3 | 2598 | 2911 | 16.36 | 2580.30 |

## Output deltas vs legacy

| variant | docs with same found count | docs with same linked count | docs with same unique found set | changed docs | extra unique mentions | missing unique mentions |
|---|---:|---:|---:|---:|---:|---:|
| async-taxonerd-whole-document-gbif | 43 | 43 | 42 | 3 | 1 | 3 |
| async-taxonerd-span-sentence-gbif | 23 | 23 | 24 | 21 | 86 | 53 |
| async-taxonerd-span-sentence-nproc2-gbif | 23 | 23 | 24 | 21 | 86 | 53 |
| async-taxonerd-span-sentence-nproc4-gbif | 23 | 23 | 24 | 21 | 86 | 53 |
| async-taxonerd-span-sentence-merged-gbif | 40 | 40 | 39 | 6 | 4 | 5 |
| async-taxonerd-span-paragraph-gbif | 31 | 31 | 26 | 19 | 38 | 36 |
| async-taxonerd-span-paragraph-nproc2-gbif | 31 | 31 | 26 | 19 | 38 | 36 |
| async-taxonerd-span-paragraph-nproc4-gbif | 31 | 31 | 26 | 19 | 38 | 36 |

## Conclusions

- The only runtime variant that beats legacy on overall median latency is whole-document runtime, and only by 1.027x.
- Whole-document runtime is slower than legacy on the large stratum: 1140 ms vs 978 ms median.
- Sentence and paragraph windowing are slower across all strata.
- Explicit spaCy `n_process` concurrency is real and was exercised, but it is worse here. The worker spawn/IPC overhead dominates the per-document span-window work.
- Response payloads are slightly smaller in the runtime variants, but runtime request payloads are much larger: about 91 KB median vs 9.8 KB for legacy. That is the clearest measured transport overhead.
- Sentence/paragraph spans change output semantics. Whole-document runtime is closest to legacy parity.

## Technical implication

For TaxoNERD, the next optimization target is not more spaCy process concurrency. The measured problem is that the generated runtime request path still pays for structural CAS input payload even when the selected strategy is whole-document text-only. The descriptor/input projection has to avoid sending spans unless the active strategy requires them; otherwise span strategies and even whole-document runtime carry avoidable process-request overhead.
