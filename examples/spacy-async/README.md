# spaCy

DUUI V1 text example with two comparable implementations:

- `spacy_legacy_annotator.py` uses the old `duui-uima/duui-spacy`
  TextImager JSON `serialize` / `deserialize` codec.
- `spacy_annotator.py` uses generated MsgPack Lua.

The annotators require spaCy and the selected spaCy model to be installed.

## Files

- `spacy_legacy_annotator.py` - old TextImager Lua JSON baseline
- `spacy_annotator.py` - generated MsgPack Lua implementation
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

Transformer analogue for the old DUUI-UIMA spaCy baseline:

```bash
python -m spacy download de_dep_news_trf
```

## Output

The annotators yield only the types declared by `TypeSystemSpacy.xml`:

```text
de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence
de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token
de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma
de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS
de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures
de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency
de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ROOT
de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity
org.texttechnologylab.annotation.SpacyAnnotatorMetaData
org.texttechnologylab.annotation.DocumentModification
```
