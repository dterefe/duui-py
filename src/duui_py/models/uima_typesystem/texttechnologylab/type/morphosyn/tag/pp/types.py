"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PPCAUSAL1(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.PPCAUSAL1"
    value: Optional[str] = None

class PPCAUSAL2(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.PPCAUSAL2"
    value: Optional[str] = None

class PPCAUSAL3(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.PPCAUSAL3"
    value: Optional[str] = None

class PPCOND1(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.PPCOND1"
    value: Optional[str] = None

class PPCOND2(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.PPCOND2"
    value: Optional[str] = None

class PPCOORA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.PPCOORA"
    value: Optional[str] = None

class PPCOORD(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.PPCOORD"
    value: Optional[str] = None

class PPPURP(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.PPPURP"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp.PPCAUSAL1": PPCAUSAL1,
    "org.texttechnologylab.type.morphosyn.tag.pp.PPCAUSAL2": PPCAUSAL2,
    "org.texttechnologylab.type.morphosyn.tag.pp.PPCAUSAL3": PPCAUSAL3,
    "org.texttechnologylab.type.morphosyn.tag.pp.PPCOND1": PPCOND1,
    "org.texttechnologylab.type.morphosyn.tag.pp.PPCOND2": PPCOND2,
    "org.texttechnologylab.type.morphosyn.tag.pp.PPCOORA": PPCOORA,
    "org.texttechnologylab.type.morphosyn.tag.pp.PPCOORD": PPCOORD,
    "org.texttechnologylab.type.morphosyn.tag.pp.PPPURP": PPPURP,
}

__all__ = [
    "PPCAUSAL1",
    "PPCAUSAL2",
    "PPCAUSAL3",
    "PPCOND1",
    "PPCOND2",
    "PPCOORA",
    "PPCOORD",
    "PPPURP",
    "UIMA_TYPE_TO_CLASS",
]
