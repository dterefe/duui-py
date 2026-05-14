# Python Config Objects

Examples define configuration directly in Python. Do not use JSON config files for new examples.

Minimal text annotator config:

```python
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    Domain,
    DomainSpec,
    IODescriptor,
)


config = AnnotatorConfig(
    meta=AnnotatorMeta(meta={"example": "my-example"}),
    descriptor=AnnotatorDescriptor(
        name="my-example",
        version="1.0.0",
        input=IODescriptor(
            text=DomainSpec(
                default=Domain(
                    mimeType="text/plain; charset=utf-8",
                    languages=["x-unspecified"],
                )
            )
        ),
        output=IODescriptor(
            types={"Taxon": ["org.texttechnologylab.annotation.type.Taxon"]},
            text=DomainSpec(
                default=Domain(
                    mimeType="text/plain; charset=utf-8",
                    languages=["x-unspecified"],
                )
            ),
        ),
    ),
    typesystem_xml_path="TypeSystem.xml",
    parameters_schema={
        "model": {"type": "string", "default": "default-model"},
    },
)
```

`typesystem_xml_path` is resolved relative to the annotator module. If the file is missing, `create_app` serves an empty type system so local smoke tests do not crash, but examples should always ship the real XML they need.

## Input Types

Use descriptor input types only when the annotator really consumes incoming annotations.

GeoNames consumes `Location` annotations:

```python
input=IODescriptor(
    types={"Location": ["de.tudarmstadt.ukp.dkpro.core.api.ner.type.Location"]},
    text=DomainSpec(default=Domain(mimeType="text/plain; charset=utf-8")),
)
```

Plain text examples such as essay scoring should not declare required input annotation types in the text domain.

## Output Types

Declare the actual UIMA types emitted by the annotator:

```python
output=IODescriptor(
    types={
        "Taxon": [
            "org.texttechnologylab.annotation.biofid.gnfinder.Taxon",
            "org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon",
        ]
    },
    text=DomainSpec(default=Domain(mimeType="text/plain; charset=utf-8")),
)
```

This descriptor is embedded in the generated Lua communication layer and is returned by `/v1/documentation`.
