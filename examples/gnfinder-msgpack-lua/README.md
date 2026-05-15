# GNFinder

DUUI V1 text example using Python-native config, generated `MsgPackLuaCodec`, and `AsyncChunkedRequestAdapter`.

## Files

- `gnfinder_annotator.py` - annotator implementation and config
- `TypeSystemGNFinder.xml` - UIMA type system
- `requirements.txt` - runtime dependencies
- `Dockerfile` - container image build
- `start.sh` - local startup helper

## Run

```bash
./start.sh
```

## Output

With `verify=true`, the annotator yields verified taxon annotations:

```text
org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon
org.texttechnologylab.annotation.AnnotatorMetaData
org.texttechnologylab.annotation.DocumentModification
```

With `verify=false`, it yields `org.texttechnologylab.annotation.biofid.gnfinder.Taxon`.
