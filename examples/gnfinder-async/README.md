# GNFinder

DUUI V1 text example with two comparable implementations:

- `gnfinder_legacy_annotator.py` uses the old custom Lua JSON codec.
- `gnfinder_annotator.py` uses generated MsgPack Lua.

## Files

- `gnfinder_legacy_annotator.py` - old Lua JSON baseline
- `gnfinder_annotator.py` - generated MsgPack Lua implementation
- `TypeSystemGNFinder.xml` - UIMA type system
- `requirements.txt` - runtime dependencies
- `Dockerfile` - container image build
- `start.sh` - local startup helper

## Run

```bash
./start.sh
```

The example calls the real `gnfinder` executable. Set `GNFINDER_BINARY` or the `gnfinder_binary` parameter if it is not on `PATH`.

## Output

The annotator yields GNFinder taxon annotations from the `names` array returned by `gnfinder`:

```text
org.texttechnologylab.annotation.biofid.gnfinder.Taxon
org.texttechnologylab.annotation.biofid.gnfinder.MetaData
org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon
org.texttechnologylab.annotation.AnnotatorMetaData
org.texttechnologylab.annotation.DocumentModification
```

When `verify=true` and GNFinder returns `verification.bestResult`, that name is emitted as `org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon`.
