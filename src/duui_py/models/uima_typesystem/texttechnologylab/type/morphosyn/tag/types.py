"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ADN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.ADN"
    value: Optional[str] = None

class CNJ(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.CNJ"
    value: Optional[str] = None

class COND3(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.COND3"
    value: Optional[str] = None

class CONJECT(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.CONJECT"
    value: Optional[str] = None

class CONV(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.CONV"
    value: Optional[str] = None

class DECL(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.DECL"
    value: Optional[str] = None

class DEDUCT(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.DEDUCT"
    value: Optional[str] = None

class DIR_INFER(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.DIR_INFER"
    value: Optional[str] = None

class EPIST(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.EPIST"
    value: Optional[str] = None

class EXPECT(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.EXPECT"
    value: Optional[str] = None

class FOC(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.FOC"
    value: Optional[str] = None

class GER(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.GER"
    value: Optional[str] = None

class HORT(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.HORT"
    value: Optional[str] = None

class IMPOSS(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.IMPOSS"
    value: Optional[str] = None

class INF(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.INF"
    value: Optional[str] = None

class IRR(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.IRR"
    value: Optional[str] = None

class IRR1(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.IRR1"
    value: Optional[str] = None

class IRR2(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.IRR2"
    value: Optional[str] = None

class KONJ1(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.KONJ1"
    value: Optional[str] = None

class NECESS1(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.NECESS1"
    value: Optional[str] = None

class NECESS2(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.NECESS2"
    value: Optional[str] = None

class NEG_morphosyn_tag_NEG(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.NEG"
    value: Optional[str] = None

class NMZ(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.NMZ"
    value: Optional[str] = None

class POSSIB(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.POSSIB"
    value: Optional[str] = None

class PP_morphosyn_tag_PP(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.PP"
    value: Optional[str] = None

class PP1(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.PP1"
    value: Optional[str] = None

class PP2(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.PP2"
    value: Optional[str] = None

class PP3(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.PP3"
    value: Optional[str] = None

class PP4(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.PP4"
    value: Optional[str] = None

class PP5(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.PP5"
    value: Optional[str] = None

class PP6(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.PP6"
    value: Optional[str] = None

class PROB(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.PROB"
    value: Optional[str] = None

class PST(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.PST"
    value: Optional[str] = None

class RETR(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.RETR"
    value: Optional[str] = None

class SPEC(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.SPEC"
    value: Optional[str] = None

class SUP(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.SUP"
    value: Optional[str] = None

class TOP(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.TOP"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.ADN": ADN,
    "org.texttechnologylab.type.morphosyn.tag.CNJ": CNJ,
    "org.texttechnologylab.type.morphosyn.tag.COND3": COND3,
    "org.texttechnologylab.type.morphosyn.tag.CONJECT": CONJECT,
    "org.texttechnologylab.type.morphosyn.tag.CONV": CONV,
    "org.texttechnologylab.type.morphosyn.tag.DECL": DECL,
    "org.texttechnologylab.type.morphosyn.tag.DEDUCT": DEDUCT,
    "org.texttechnologylab.type.morphosyn.tag.DIR_INFER": DIR_INFER,
    "org.texttechnologylab.type.morphosyn.tag.EPIST": EPIST,
    "org.texttechnologylab.type.morphosyn.tag.EXPECT": EXPECT,
    "org.texttechnologylab.type.morphosyn.tag.FOC": FOC,
    "org.texttechnologylab.type.morphosyn.tag.GER": GER,
    "org.texttechnologylab.type.morphosyn.tag.HORT": HORT,
    "org.texttechnologylab.type.morphosyn.tag.IMPOSS": IMPOSS,
    "org.texttechnologylab.type.morphosyn.tag.INF": INF,
    "org.texttechnologylab.type.morphosyn.tag.IRR": IRR,
    "org.texttechnologylab.type.morphosyn.tag.IRR1": IRR1,
    "org.texttechnologylab.type.morphosyn.tag.IRR2": IRR2,
    "org.texttechnologylab.type.morphosyn.tag.KONJ1": KONJ1,
    "org.texttechnologylab.type.morphosyn.tag.NECESS1": NECESS1,
    "org.texttechnologylab.type.morphosyn.tag.NECESS2": NECESS2,
    "org.texttechnologylab.type.morphosyn.tag.NEG": NEG_morphosyn_tag_NEG,
    "org.texttechnologylab.type.morphosyn.tag.NMZ": NMZ,
    "org.texttechnologylab.type.morphosyn.tag.POSSIB": POSSIB,
    "org.texttechnologylab.type.morphosyn.tag.PP": PP_morphosyn_tag_PP,
    "org.texttechnologylab.type.morphosyn.tag.PP1": PP1,
    "org.texttechnologylab.type.morphosyn.tag.PP2": PP2,
    "org.texttechnologylab.type.morphosyn.tag.PP3": PP3,
    "org.texttechnologylab.type.morphosyn.tag.PP4": PP4,
    "org.texttechnologylab.type.morphosyn.tag.PP5": PP5,
    "org.texttechnologylab.type.morphosyn.tag.PP6": PP6,
    "org.texttechnologylab.type.morphosyn.tag.PROB": PROB,
    "org.texttechnologylab.type.morphosyn.tag.PST": PST,
    "org.texttechnologylab.type.morphosyn.tag.RETR": RETR,
    "org.texttechnologylab.type.morphosyn.tag.SPEC": SPEC,
    "org.texttechnologylab.type.morphosyn.tag.SUP": SUP,
    "org.texttechnologylab.type.morphosyn.tag.TOP": TOP,
}

__all__ = [
    "ADN",
    "CNJ",
    "COND3",
    "CONJECT",
    "CONV",
    "DECL",
    "DEDUCT",
    "DIR_INFER",
    "EPIST",
    "EXPECT",
    "FOC",
    "GER",
    "HORT",
    "IMPOSS",
    "INF",
    "IRR",
    "IRR1",
    "IRR2",
    "KONJ1",
    "NECESS1",
    "NECESS2",
    "NEG_morphosyn_tag_NEG",
    "NMZ",
    "POSSIB",
    "PP_morphosyn_tag_PP",
    "PP1",
    "PP2",
    "PP3",
    "PP4",
    "PP5",
    "PP6",
    "PROB",
    "PST",
    "RETR",
    "SPEC",
    "SUP",
    "TOP",
    "UIMA_TYPE_TO_CLASS",
]
