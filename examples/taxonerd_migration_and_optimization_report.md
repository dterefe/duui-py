# TaxoNERD Migration And Optimization Report

## Current State

The most up-to-date legacy reference in this workspace is `duui-uima/duui-taxoNERD`.
Its actual service contract is:

- request fields: `text`, `linking`, `threshold`, `exclude`, `model`
- default model: `en_ner_eco_md`
- default linker: `gbif_backbone`
- default excluded pipeline components: `tagger`, `parser`, `taxo_abbrev_detector`, `taxon_linker`, `pysbd_sentencizer`
- output: taxon spans plus linker comments (`id`, `value`, `propability`)
- Docker image installs the four released TaxoNERD model wheels from the `v1.5.4` release.

The DUUI-Py legacy implementation was not a faithful migration before this pass. It accepted only `text`, used environment-style defaults that did not match DUUI-UIMA, and did not forward `model`, `linking`, `threshold`, or `exclude` from Lua. That would have made a legacy-vs-v2 evaluation semantically invalid.

## Changes Prepared

- `examples/taxonerd-legacy-lua/taxonerd_legacy_annotator.py`
  - now accepts and forwards the DUUI-UIMA request fields
  - uses DUUI-UIMA defaults
  - loads TaxoNERD through `TaxoNERD(...).load(...)`, matching the current DUUI-UIMA service shape
  - supports `en_ner_eco_md`, `en_ner_eco_md_weak`, `en_ner_eco_biobert`, and `en_ner_eco_biobert_weak`
  - keeps the legacy Lua-visible response while also keeping the richer migrated metadata fields

- `examples/taxonerd-legacy-lua/communication.lua`
  - now serializes `model`, `linking`, `threshold`, and `exclude` from DUUI parameters
  - matches the DUUI-UIMA Lua request behavior

- `examples/taxonerd-legacy-lua/Dockerfile`
  - switched to the Python 3.10 + build-dependency pattern used by DUUI-UIMA
  - installs TaxoNERD and the four released model wheels

- `examples/taxonerd-msgpack-lua/taxonerd_annotator.py`
  - now accepts weak model aliases too

- `examples/taxonerd-msgpack-lua/taxonerd_span_window_annotator.py`
  - now accepts weak model aliases too

- `examples/taxonerd_evaluation_configurations.json`
  - defines the evaluation variants and telemetry metrics to collect.

## Optimization Avenues

### 1. Legacy Parity Baseline

Use `taxonerd-legacy-lua` with the exact DUUI-UIMA defaults. This is the only valid baseline for functional and semantic parity.

Measure:

- `duui.request.duration` p50/p90/p95/p99
- `duui.request.throughput`
- `taxonerd_legacy_processing_ms`
- CPU and memory telemetry
- normalized Taxon span/linker equivalence against DUUI-UIMA output

### 2. Legacy With Greedy Async DUUI Dispatch

This does not change the annotator semantics. It tests orchestration utilization.

Use the rework runtime style already present in `DUUIDistributedBiofidPipelineTest`:

```java
taxonerd.dispatchPolicy(DUUIDispatchPolicy.of(DUUIDispatchMode.IO, parallelism));
builder.concurrency(...).scale(...);
```

This is the cleanest first optimization because it can improve throughput without changing input domain, model, linker, or output semantics.

### 3. V2 Whole Document MsgPack/Lua

Use `taxonerd_annotator.py` as the protocol migration baseline. This tests whether generated MsgPack/Lua plus async request handling changes overhead relative to legacy JSON Lua.

This variant is semantically closest to legacy because it still receives full document text.

### 4. V2 Span/Window Input

Use `taxonerd_span_window_annotator.py`.

Main idea: TaxoNERD is expensive on long noisy OCR documents. Instead of sending one large full document, consume existing UIMA spans and batch bounded windows through `nlp.pipe`.

Candidate span domains:

- `sentence`: best for predictable bounded windows and high pipeline parallelism
- `paragraph` / `ocr_paragraph`: better context, fewer windows, often better semantic quality
- `div`, `section`, `title`: useful fallback for already structured documents

Metrics to compare:

- latency tails per document
- total request throughput
- `taxonerd_span_window_processing_ms`
- windows per document (`taxonerd_span_window_windows`)
- CPU utilization under batch sizes 4/8/16
- memory RSS/USS under whole-document vs span-window
- normalized output drift caused by windowing

### 5. NER-Only / No-Linker Variant

Use span-window with:

```json
{
  "linking": "none",
  "with_abbrev": false,
  "ner_only": true
}
```

This separates pure NER/model cost from entity-linking cost. It is important because linker choice can dominate tail latency and can change output semantics.

### 6. Model Weight Variants

Evaluate at least:

- `en_ner_eco_md`
- `en_ner_eco_md_weak`
- `en_ner_eco_biobert` if GPU or a long CPU window is available
- `en_ner_eco_biobert_weak` if the professor cares about heavier model tradeoffs

The `md` variants are the fastest path for near-term evaluation. BioBERT should not be mixed into the first performance claim unless hardware and warmup are controlled.

## Correctness Gate Before Performance Claims

Before presenting performance numbers, normalize every variant to:

```text
begin, end, covered_text, linker_id(s), linker_value(s), probability
```

Then classify differences:

- exact match
- same span, different linker
- shifted span
- span only in baseline
- span only in variant

Only after this gate should latency/throughput/resource numbers be interpreted.

## Recommended Next Run

Run the following in order:

1. `legacy-uima-parity`
2. `legacy-uima-parity-async-greedy`
3. `v2-whole-document-md-gbif`
4. `v2-span-window-sentence-md-gbif`
5. `v2-span-window-paragraph-md-gbif`
6. `v2-span-window-ner-only-md`

Use 5-10 XMI documents first, then repeat with more documents once TaxoNERD startup/warmup and model cache behavior are stable.

## Upstream TaxoNERD Fork Direction

Current upstream TaxoNERD is a thin but useful wrapper around spaCy:

- load a taxonomic NER spaCy pipeline such as `en_ner_eco_md`
- optionally add abbreviation/sentence components
- optionally add a linker such as `gbif_backbone`
- filter `doc.ents` to TaxoNERD's `LIVB` label
- output offsets plus linker candidates

The linker is already the separable part. Its core operation is candidate generation over unique mention strings, with a threshold over candidate similarity. That means the best BIOFID-specific optimization is not just "make TaxoNERD faster"; it is to split TaxoNERD into explicit modes:

1. `ner-sentence-batched`: use existing UIMA `Sentence` annotations as individual TaxoNERD input items and process them via `nlp.pipe(batch_size=N)`.
2. `ner-window-batched`: optionally merge nearby sentence/paragraph spans into bounded windows and process selected windows via `nlp.pipe(batch_size=N)`.
3. `precomputed-entity-link-only`: consume existing UIMA entity spans from the earlier BIOFID spaCy stage, skip TaxoNERD NER, batch unique mention strings through the GBIF linker, and emit `Taxon`.
4. `hybrid`: if usable upstream entities exist, link them; otherwise fall back to `ner-sentence-batched`.

The first local prototype for mode 2 is:

```text
examples/taxonerd-msgpack-lua/taxonerd_precomputed_entity_annotator.py
```

It accepts existing `NamedEntity` / `Taxon`-like spans, runs batched TaxoNERD candidate generation with `gbif_backbone`, and emits normal `org.texttechnologylab.annotation.type.Taxon` annotations. Telemetry focuses on the metrics that matter for this comparison:

- `taxonerd_precomputed_entity_candidates`
- `taxonerd_precomputed_entity_taxon_matches`
- `taxonerd_precomputed_entity_linked_mentions`
- `taxonerd_precomputed_entity_processing_ms`

Recommended DUUI parameters:

For the sentence-batched NER optimization:

```json
{
  "model": "en_ner_eco_md",
  "linking": "gbif_backbone",
  "threshold": 0.7,
  "span_types": ["sentence"],
  "merge_spans": false,
  "batch_size": 8
}
```

For the precomputed entity linker:

```json
{
  "linking": "gbif_backbone",
  "threshold": 0.7,
  "neighbours": 10,
  "entity_types": [
    "org.texttechnologylab.annotation.NamedEntity",
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity",
    "org.texttechnologylab.annotation.type.Taxon"
  ],
  "entity_labels": []
}
```

The fork should expose this split as library API, not only as a DUUI wrapper:

- `TaxoNERD.pipe_texts(texts, batch_size=...)`
- `TaxoNERD.link_mentions(mentions, linker="gbif_backbone", threshold=0.7, k=10)`
- `TaxoNERD.link_doc_entities(doc)` for already-created spaCy `Doc` objects
- a dependency refresh for current Python/spaCy without importing document-conversion extras on the hot path

Important risk: if the prior BIOFID spaCy stage only writes generic NER spans without token/lemma features, the link-only path still works by linking covered mention strings directly. If the prior stage can persist token/lemma features later, the fork can switch to TaxoNERD's lemma-normalized mention strings for closer parity with the original linker.
