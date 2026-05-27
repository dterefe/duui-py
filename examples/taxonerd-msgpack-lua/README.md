# TaxoNERD

DUUI V1 text example using Python-native config, generated `MsgPackLuaCodec`, and `AsyncChunkedRequestAdapter`.

The `input_strategy=legacy-procedure` variant intentionally uses the same TaxoNERD
procedure as the legacy service: load TaxoNERD with the configured linker and call
`find_in_text(text)`. It exists to compare legacy JSON/Lua transport against the
generated MsgPack/async transport without changing the TaxoNERD algorithm.

## Files

- `taxonerd_annotator.py` - whole-document baseline annotator implementation and config
- `taxonerd_span_window_annotator.py` - experimental span/window annotator that consumes UIMA sentence/paragraph/div/section/title spans, batches bounded windows, and remaps TaxoNERD offsets to the original document
- `TypeSystem*.xml` - UIMA type system
- `requirements.txt` - runtime dependencies
- `Dockerfile` - container image build
- `start.sh` - local startup helper

## Run

```bash
./start.sh
```

## Output

The annotator yields existing UIMA model objects:

```text
org.texttechnologylab.annotation.type.Taxon
org.texttechnologylab.annotation.AnnotatorMetaData
org.texttechnologylab.annotation.DocumentModification
```
