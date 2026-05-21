# Example Annotators

The examples are the contract for the currently documented framework surface.

All current Python examples define config in code, use generated `MsgPackLuaCodec`, pass `AsyncChunkedRequestAdapter` to `create_app`, log normal lifecycle messages, emit metrics, and yield existing UIMA model objects. They do not use custom Lua scripts.

## GNFinder

Path:

```text
examples/gnfinder-msgpack-lua
```

Uses:

- plain text input
- `GNFinderTaxon`
- `VerifiedTaxon` when `verify=true` and GNFinder returns `verification.bestResult`
- BIOfid/GNFinder type system XML
- a real `gnfinder` executable via `GNFINDER_BINARY`, `PATH`, or the `gnfinder_binary` parameter

Example output:

```text
org.texttechnologylab.annotation.biofid.gnfinder.Taxon [0, 12] "Homo sapiens"
org.texttechnologylab.annotation.biofid.gnfinder.Taxon [17, 29] "Panthera leo"
```

## TaxoNERD

Path:

```text
examples/taxonerd-msgpack-lua
```

Uses `org.texttechnologylab.annotation.type.Taxon`.

Example output:

```text
org.texttechnologylab.annotation.type.Taxon [0, 12] "Homo sapiens"
```

## Argument

Path:

```text
examples/argument-msgpack-lua
```

Uses:

- `org.texttechnologylab.annotation.Argument` as an annotation
- `org.texttechnologylab.annotation.AnnotationComment` as a feature structure

Example output:

```text
org.texttechnologylab.annotation.Argument [0, 60]
  topic = "biodiversity"
  reason = "pos=3, neg=0, topic_hit=1"
```

## Essay Scorer

Path:

```text
examples/essay-scorer-msgpack-lua
```

Uses `org.texttechnologylab.annotation.EssayScore`.

Example output:

```text
org.texttechnologylab.annotation.EssayScore [0, 67]
  Name = "EssayScore"
  Value = 2.41
```

## SRL

Path:

```text
examples/srl-msgpack-lua
```

Uses:

- `org.texttechnologylab.annotation.semaf.isobase.Entity`
- `org.texttechnologylab.annotation.semaf.semafsr.SrLink`

Example output:

```text
org.texttechnologylab.annotation.semaf.isobase.Entity [0, 11] "Researchers"
org.texttechnologylab.annotation.semaf.semafsr.SrLink
  rel_type = "ARG0"
```

## spaCy

Path:

```text
examples/spacy-lua-msgpack
```

Uses DKPro segmentation, POS, morphology, named entity, and dependency types.

Example output:

```text
de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence [0, 20]
de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token [0, 9] "Frankfurt"
```

## GeoNames

Path:

```text
examples/geonames-msgpack-lua
```

Uses:

- incoming `de.tudarmstadt.ukp.dkpro.core.api.ner.type.Location`
- outgoing `org.texttechnologylab.annotation.geonames.GeoNamesEntity`
- a real `duui-geonames-fst` compatible backend via `backend_url`

Example output:

```text
org.texttechnologylab.annotation.geonames.GeoNamesEntity [0, 17] "Frankfurt am Main"
  name = "Frankfurt am Main"
  countryCode = "DE"
```

## Whisper

Path:

```text
examples/whisper-msgpack-lua
```

Uses byte SofA input and `process_bytes`.

Example output:

```text
org.texttechnologylab.annotation.type.AudioToken [0, 1200]
  value = "transcribed text"
```
