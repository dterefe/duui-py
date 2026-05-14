# spaCy MsgPack Lua Example

This example uses the standard `MsgPackLuaCodec`. The Lua communication layer is generated from the annotator descriptor, so there is no handwritten Lua script to keep in sync.

The annotator uses spaCy when it is installed and falls back to deterministic lightweight token, sentence, lemma, POS, morphology, dependency, and named-entity annotations when spaCy is unavailable.

## Files

- `spacy_annotator.py` - annotator implementation and in-code Python config
- `TypeSystemSpacy.xml` - UIMA type system
- `annotator_config.json` - legacy reference config, not used by the Python example
- `requirements.txt` - optional example dependencies

## Run

```bash
cd examples/spacy-lua-msgpack
uvicorn spacy_annotator:app --host 0.0.0.0 --port 9714
```

Optional spaCy model:

```bash
python -m spacy download en_core_web_sm
```
