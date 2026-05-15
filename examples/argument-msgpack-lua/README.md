# Argument Classification

DUUI V1 text example using Python-native config, generated `MsgPackLuaCodec`, and `AsyncChunkedRequestAdapter`.

## Files

- `argument_annotator.py` - annotator implementation and config
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
org.texttechnologylab.annotation.Argument
org.texttechnologylab.annotation.AnnotationComment
org.texttechnologylab.annotation.AnnotatorMetaData
org.texttechnologylab.annotation.DocumentModification
```
