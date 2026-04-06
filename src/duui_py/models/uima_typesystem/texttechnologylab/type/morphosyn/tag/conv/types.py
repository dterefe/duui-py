"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVANT(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVANT"
    value: Optional[str] = None

class CONVANT1(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVANT1"
    value: Optional[str] = None

class CONVANT2(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVANT2"
    value: Optional[str] = None

class CONVBACKG(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVBACKG"
    value: Optional[str] = None

class CONVCAUSAL(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCAUSAL"
    value: Optional[str] = None

class CONVCON(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCON"
    value: Optional[str] = None

class CONVCONC(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCONC"
    value: Optional[str] = None

class CONVCONCCOND(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCONCCOND"
    value: Optional[str] = None

class CONVCOND(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOND"
    value: Optional[str] = None

class CONVCOND1(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOND1"
    value: Optional[str] = None

class CONVCOND2(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOND2"
    value: Optional[str] = None

class CONVCOOR(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOOR"
    value: Optional[str] = None

class CONVCOORA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOORA"
    value: Optional[str] = None

class CONVCOORD(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOORD"
    value: Optional[str] = None

class CONVDE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVDE"
    value: Optional[str] = None

class CONVMAN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVMAN"
    value: Optional[str] = None

class CONVNEG(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVNEG"
    value: Optional[str] = None

class CONVPOST(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVPOST"
    value: Optional[str] = None

class CONVPURP1(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVPURP1"
    value: Optional[str] = None

class CONVPURP2(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVPURP2"
    value: Optional[str] = None

class CONVPURP3(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVPURP3"
    value: Optional[str] = None

class CONVSIM(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.CONVSIM"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVANT": CONVANT,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVANT1": CONVANT1,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVANT2": CONVANT2,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVBACKG": CONVBACKG,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCAUSAL": CONVCAUSAL,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCON": CONVCON,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCONC": CONVCONC,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCONCCOND": CONVCONCCOND,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOND": CONVCOND,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOND1": CONVCOND1,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOND2": CONVCOND2,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOOR": CONVCOOR,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOORA": CONVCOORA,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVCOORD": CONVCOORD,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVDE": CONVDE,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVMAN": CONVMAN,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVNEG": CONVNEG,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVPOST": CONVPOST,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVPURP1": CONVPURP1,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVPURP2": CONVPURP2,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVPURP3": CONVPURP3,
    "org.texttechnologylab.type.morphosyn.tag.conv.CONVSIM": CONVSIM,
}

__all__ = [
    "CONVANT",
    "CONVANT1",
    "CONVANT2",
    "CONVBACKG",
    "CONVCAUSAL",
    "CONVCON",
    "CONVCONC",
    "CONVCONCCOND",
    "CONVCOND",
    "CONVCOND1",
    "CONVCOND2",
    "CONVCOOR",
    "CONVCOORA",
    "CONVCOORD",
    "CONVDE",
    "CONVMAN",
    "CONVNEG",
    "CONVPOST",
    "CONVPURP1",
    "CONVPURP2",
    "CONVPURP3",
    "CONVSIM",
    "UIMA_TYPE_TO_CLASS",
]
