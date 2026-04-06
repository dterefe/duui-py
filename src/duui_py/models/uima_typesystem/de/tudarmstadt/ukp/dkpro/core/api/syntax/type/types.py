"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.syntax.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PennTree(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.PennTree"
    PennTree: Optional[str] = None
    TransformationNames: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.PennTree": PennTree,
}

__all__ = [
    "PennTree",
    "UIMA_TYPE_TO_CLASS",
]
