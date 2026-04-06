"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.adn."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ADNIRR(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.adn.ADNIRR"
    value: Optional[str] = None

class ADNREAL(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.adn.ADNREAL"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.adn.ADNIRR": ADNIRR,
    "org.texttechnologylab.type.morphosyn.tag.adn.ADNREAL": ADNREAL,
}

__all__ = [
    "ADNIRR",
    "ADNREAL",
    "UIMA_TYPE_TO_CLASS",
]
