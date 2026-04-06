"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.adn.adnreal."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ADNREALKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.adn.adnreal.ADNREALKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.adn.adnreal.ADNREALKO": ADNREALKO,
}

__all__ = [
    "ADNREALKO",
    "UIMA_TYPE_TO_CLASS",
]
