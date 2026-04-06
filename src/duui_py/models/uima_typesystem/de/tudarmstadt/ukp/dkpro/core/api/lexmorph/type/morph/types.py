"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Morpheme(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.Morpheme"
    morphTag: Optional[str] = None

class MorphologicalFeatures(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures"
    animacy: Optional[str] = None
    aspect: Optional[str] = None
    case: Optional[str] = None
    definiteness: Optional[str] = None
    degree: Optional[str] = None
    gender: Optional[str] = None
    mood: Optional[str] = None
    negative: Optional[str] = None
    numType: Optional[str] = None
    number: Optional[str] = None
    person: Optional[str] = None
    possessive: Optional[str] = None
    pronType: Optional[str] = None
    reflex: Optional[str] = None
    tense: Optional[str] = None
    transitivity: Optional[str] = None
    value: Optional[str] = None
    verbForm: Optional[str] = None
    voice: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.Morpheme": Morpheme,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures": MorphologicalFeatures,
}

__all__ = [
    "Morpheme",
    "MorphologicalFeatures",
    "UIMA_TYPE_TO_CLASS",
]
