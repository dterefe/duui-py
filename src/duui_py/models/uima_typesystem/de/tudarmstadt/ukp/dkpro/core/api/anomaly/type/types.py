"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.anomaly.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Anomaly(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.anomaly.type.Anomaly"
    category: Optional[str] = None
    description: Optional[str] = None
    suggestions: Optional[list[UimaValue]] = None

class GrammarAnomaly(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.anomaly.type.GrammarAnomaly"
    category: Optional[str] = None
    description: Optional[str] = None
    suggestions: Optional[list[UimaValue]] = None

class SpellingAnomaly(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.anomaly.type.SpellingAnomaly"
    category: Optional[str] = None
    description: Optional[str] = None
    suggestions: Optional[list[UimaValue]] = None

class SuggestedAction(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.anomaly.type.SuggestedAction"
    certainty: Optional[float] = None
    replacement: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.anomaly.type.Anomaly": Anomaly,
    "de.tudarmstadt.ukp.dkpro.core.api.anomaly.type.GrammarAnomaly": GrammarAnomaly,
    "de.tudarmstadt.ukp.dkpro.core.api.anomaly.type.SpellingAnomaly": SpellingAnomaly,
    "de.tudarmstadt.ukp.dkpro.core.api.anomaly.type.SuggestedAction": SuggestedAction,
}

__all__ = [
    "Anomaly",
    "GrammarAnomaly",
    "SpellingAnomaly",
    "SuggestedAction",
    "UIMA_TYPE_TO_CLASS",
]
