from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Any
from typing_extensions import TypedDict

FeatureStructureRef = TypedDict("FeatureStructureRef", {"$ref": int})
PackedFloat32Array = TypedDict("PackedFloat32Array", {"$f32": bytes})
PackedFloat64Array = TypedDict("PackedFloat64Array", {"$f64": bytes})
PackedInt32Array = TypedDict("PackedInt32Array", {"$i32": bytes})
PackedInt64Array = TypedDict("PackedInt64Array", {"$i64": bytes})

# Simplified type to avoid recursion issues in Pydantic
# Original recursive type caused infinite recursion
UimaValue = Any


class FeatureStructure(BaseModel):
    ref: Optional[int] = None
    type: str
    features: dict[str, UimaValue] = Field(default_factory=dict)


class Annotation(FeatureStructure):
    begin: int
    end: int = Field(alias="end")


class Sentence(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"


class Token(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"


class Lemma(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.Lemma"


class POS(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"


class NamedEntity(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"
