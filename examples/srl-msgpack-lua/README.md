# Semantic Role Labeling

DUUI V1 text example using Python-native config, generated `MsgPackLuaCodec`, and `AsyncChunkedRequestAdapter`.

## Files

- `srl_annotator.py` - annotator implementation and config
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
org.texttechnologylab.annotation.semaf.isobase.Entity
org.texttechnologylab.annotation.semaf.semafsr.SrLink
org.texttechnologylab.annotation.AnnotatorMetaData
org.texttechnologylab.annotation.DocumentModification
```
