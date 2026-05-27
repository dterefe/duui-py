# Chunked Lua Wire Matrix

This matrix is for comparing DUUI legacy annotators against descriptor-driven
duui-py annotators without changing the legacy Java transport path. Legacy
annotators must run through their original buffered JSON/Lua protocol. New
duui-py annotators may use the V1 streaming transport, but the benchmark output
must label that as a different execution mode.

## Expected Async Bound

If response deserialization is 30% of total request time, perfect overlap gives
at most `1 / (1 - 0.30) = 1.43x` for a single document when annotator processing
and deserialization can be fully overlapped. Anything above that must come from
removing protocol overhead, reducing payload bytes, cheaper Lua apply loops,
less CAS indexing cost, less queueing, or better multi-document scheduling. A
small async-only delta is therefore not proof of failure; a small total delta
after protocol overhead has also been removed is the actual failure signal.

## Configurations

Every result row must include these labels:

- `protocol`: `legacy-json-lua`, `generated-msgpack-windowed`, `runtime-msgpack-columnar`,
  `runtime-msgpack-windowed`, `runtime-msgpack-packed`, or `runtime-msgpack-compressed`.
- `java_transport`: `legacy-buffered` or `v1-streaming`.
- `java_executor`: `platform` or `virtual`.
- `document_mode`: `single-doc` or `multi-doc`.
- `chunk_rows`, `chunk_bytes`, and `compression`.

Legacy rows are always:

- `protocol=legacy-json-lua`
- `java_transport=legacy-buffered`
- no response windowing
- no async deserialize/apply
- same profiling labels where the stage exists, and `not_applicable` where it
  does not.

## Reusable Lua Runtime Design

The next codec should stop generating a full per-annotator Lua script. It should
ship one reusable Lua runtime plus a compact descriptor manifest. The manifest is
the only annotator-specific data.

Generic frame header:

- byte `kind`
- uint32 `payload_len`
- uint32 `sequence`
- uint16 `flags`
- uint16 `type_id` when the frame is type-scoped, otherwise `0`
- uint32 `row_count` when the frame is tabular, otherwise `0`

Frame kinds:

- `START`: protocol version, descriptor hash, type table, feature table, range table.
- `SOFA`: document text or bytes.
- `TYPE_BATCH_ROW`: generic rows `[ref, begin, end, feature...]`.
- `TYPE_BATCH_COLUMN`: columns `begin[]`, `end[]`, one column per feature.
- `TYPE_BATCH_PACKED`: primitive columns packed as bytes for int/long/float/bool.
- `REF_PATCH`: stable local FS id to target id patches.
- `METRIC`: optional profile counters emitted by the annotator side.
- `ERROR`: structured failure.
- `END`: stream terminator.

Lua runtime responsibilities:

- cache UIMA types, feature handles, constructors, and index mode once.
- read the manifest into type/feature/range tables.
- use one generic batch applier for all annotators.
- select direct primitive setters from range metadata.
- apply each window immediately, then patch unresolved references at window or
  stream end.
- never branch on `spaCy`, `taxonerd`, `Token`, `Sentence`, DKPro class names, or
  annotator-specific semantics.

Descriptor manifest responsibilities:

- assign stable integer type IDs.
- assign per-type feature IDs.
- mark primitive ranges, reference ranges, arrays, and string-heavy columns.
- declare required input projection and output projection.
- declare chunk caps and compression mode.

## Protocol Variants

- `runtime-msgpack-columnar`: one type batch per type, columns in MsgPack arrays.
- `runtime-msgpack-windowed`: same data layout, bounded by rows and bytes; default
  candidate for large CAS output because Java can apply early.
- `runtime-msgpack-packed`: begin/end/ref/int/bool/float columns packed as binary
  arrays, strings and unknown features remain MsgPack arrays.
- `runtime-msgpack-compressed`: windowed columnar with low-level compression only
  when network/response bytes dominate; never default by assumption.
- `generated-msgpack-windowed`: current generated Lua baseline.
- `legacy-json-lua`: old DUUI annotator protocol baseline.

## Profiling Phases

Python annotator side:

- request stream read
- request chunk decode
- annotator process start to first output
- annotator process total
- response batch build
- response MsgPack pack
- response compression
- response first frame
- response total encode
- response payload bytes and frame bytes

Java/DUUI side:

- Lua request serialization
- request bytes
- HTTP send/receive
- first response byte
- first response chunk
- first CAS apply
- response receive total
- Lua deserialize/apply total
- response bytes
- CAS type counts and annotation counts
- total component latency

Legacy Java rows still report the common phases, but `first response chunk` and
`first CAS apply` are expected to be unavailable because the old path is
buffered.

## Platform vs Virtual Threads

Virtual-thread comparisons belong in the orchestration/executor configuration,
not in the wire format. The same protocol and chunk settings must be run with:

- platform executor, single document
- virtual executor, single document
- platform executor, multiple documents
- virtual executor, multiple documents

For a single CPU-bound document, virtual threads are expected to help only if the
pipeline currently blocks while waiting for chunks or handoff. For many
documents, virtual threads can improve queueing and blocking behavior while the
actual CAS apply work remains bounded by CPU cores.

## Optimization Order

1. Make legacy and modern timings comparable with identical phase names.
2. Make current generated MsgPack overhead visible: rows, chunks, payload bytes,
   batch build, pack, compression, and decode/apply.
3. Build `runtime-msgpack-columnar` as the reusable Lua runtime baseline.
4. Add windowed apply and show first-annotation application before full response.
5. Add packed primitive columns only after columnar hotspots are proven.
6. Add virtual-thread comparison after chunked apply is already correct and
   faster on platform threads.
7. Expand from single-document to multi-document throughput/tail latency.
