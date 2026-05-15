# Whisper

DUUI V1 byte-SofA example using Python-native config, generated `MsgPackLuaCodec`, and `AsyncChunkedRequestAdapter`.

## Files

- `whisper_annotator.py` - annotator implementation and config
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
org.texttechnologylab.annotation.type.AudioToken
org.texttechnologylab.annotation.AnnotatorMetaData
org.texttechnologylab.annotation.DocumentModification
```
