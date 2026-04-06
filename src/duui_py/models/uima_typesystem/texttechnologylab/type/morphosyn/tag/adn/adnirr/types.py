"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.adn.adnirr."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ADNIRRKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.adn.adnirr.ADNIRRKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.adn.adnirr.ADNIRRKO": ADNIRRKO,
}

__all__ = [
    "ADNIRRKO",
    "UIMA_TYPE_TO_CLASS",
]
