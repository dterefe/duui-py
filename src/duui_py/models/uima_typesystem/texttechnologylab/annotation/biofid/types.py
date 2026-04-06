"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.biofid."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Taxon(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.Taxon"
    identifier: Optional[str] = None
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.biofid.Taxon": Taxon,
}

__all__ = [
    "Taxon",
    "UIMA_TYPE_TO_CLASS",
]
