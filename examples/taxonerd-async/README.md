# TaxoNERD

DUUI V1 text example with two comparable implementations:

- `taxonerd_legacy_annotator.py` uses the old custom Lua JSON codec.
- `taxonerd_annotator.py` uses generated MsgPack Lua.

Both versions load TaxoNERD from the GitHub Abrami fork and call the same
`find_in_text(text)` procedure. That keeps evaluation focused on DUUI transport
and procedural overhead instead of changing model or linker semantics.

## Files

- `taxonerd_legacy_annotator.py` - old Lua JSON baseline
- `taxonerd_annotator.py` - generated MsgPack Lua implementation
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
org.texttechnologylab.annotation.AnnotationComment
```
