"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.semantics.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class SemArg(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemArg"
    pass

class SemArgLink(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemArgLink"
    role: Optional[str] = None
    target: Optional[UimaValue] = None

class SemPred(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemPred"
    arguments: Optional[list[UimaValue]] = None
    category: Optional[str] = None

class SemanticArgument(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemanticArgument"
    role: Optional[str] = None

class SemanticField(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemanticField"
    value: Optional[str] = None

class SemanticPredicate(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemanticPredicate"
    arguments: Optional[list[UimaValue]] = None
    category: Optional[str] = None

class WordSense(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.WordSense"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemArg": SemArg,
    "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemArgLink": SemArgLink,
    "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemPred": SemPred,
    "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemanticArgument": SemanticArgument,
    "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemanticField": SemanticField,
    "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemanticPredicate": SemanticPredicate,
    "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.WordSense": WordSense,
}

__all__ = [
    "SemArg",
    "SemArgLink",
    "SemPred",
    "SemanticArgument",
    "SemanticField",
    "SemanticPredicate",
    "WordSense",
    "UIMA_TYPE_TO_CLASS",
]
