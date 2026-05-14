# UIMA Models and Type Systems

Examples should use the model classes already generated under:

```text
src/duui_py/models/uima_typesystem
```

Do not invent local annotation classes in examples.

## Importing Models

GNFinder:

```python
from duui_py.models.uima_typesystem.texttechnologylab.annotation.biofid.gnfinder.types import (
    GNFinderTaxon,
    VerifiedTaxon,
)
```

GeoNames:

```python
from duui_py.models.uima_typesystem.texttechnologylab.annotation.geonames.types import GeoNamesEntity
```

DKPro segmentation:

```python
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.types import (
    Sentence,
    Token,
)
```

## Creating Annotations

```python
annotations = [
    VerifiedTaxon(
        begin=0,
        end=12,
        value="Homo sapiens",
        cardinality=2,
        oddsLog10=0.75,
        matchedName="Homo sapiens",
        matchedCanonicalSimple="Homo sapiens",
        matchedCanonicalFull="Homo sapiens",
        currentName="Homo sapiens",
        dataSourceId=0,
        recordId="heuristic-0-12",
        sortScore=0.75,
        editDistance=0,
    )
]
```

Output:

```text
org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon [0, 12]
  value = "Homo sapiens"
  cardinality = 2
  matchedName = "Homo sapiens"
```

## Type-System XML

Each example ships the XML needed by DUUI Java to create the CAS:

```text
examples/gnfinder-msgpack-lua/TypeSystemGNFinder.xml
examples/geonames-msgpack-lua/TypeSystemGeoNames.xml
```

The current source of truth is the local UIMA type-system library used by DUUI:

```text
/home/stud_homes/s0424382/projects/ttlab/uce/biofid-nova-preprocessing/UIMATypeSystem
```

`duui-py` model coverage has been checked against that type system plus the installed BIOfid 3.0.14 definitions.
