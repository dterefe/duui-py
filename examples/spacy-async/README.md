# spaCy

DUUI V1 text example using Python-native config, generated `MsgPackLuaCodec`, and `AsyncChunkedRequestAdapter`.

The annotator uses spaCy when it is installed and falls back to deterministic lightweight token, sentence, lemma, POS, morphology, dependency, and named-entity annotations when spaCy is unavailable.

## Files

- `spacy_annotator.py` - annotator implementation and config
- `TypeSystemSpacy.xml` - UIMA type system
- `requirements.txt` - optional example dependencies
- `Dockerfile` - container image build
- `start.sh` - local startup helper

## Run

```bash
./start.sh
```

Optional spaCy model:

```bash
python -m spacy download en_core_web_sm
```

## Output

The annotator yields existing DKPro model objects:

```text
de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence
de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token
de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS
de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity
org.texttechnologylab.annotation.AnnotatorMetaData
org.texttechnologylab.annotation.DocumentModification
```
