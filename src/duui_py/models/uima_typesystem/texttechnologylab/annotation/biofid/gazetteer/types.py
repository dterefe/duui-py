"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.biofid.gazetteer."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Taxon_biofid_gazetteer_Taxon(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.gazetteer.Taxon"
    identifier: Optional[str] = None
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.biofid.gazetteer.Taxon": Taxon_biofid_gazetteer_Taxon,
}

__all__ = [
    "Taxon_biofid_gazetteer_Taxon",
    "UIMA_TYPE_TO_CLASS",
]
