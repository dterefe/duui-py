"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ADJP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.ADJP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class ADVP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.ADVP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class CONJP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.CONJP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class Constituent(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.Constituent"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class FRAG(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.FRAG"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class INTJ_type_constituent_INTJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.INTJ"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class LST_type_constituent_LST(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.LST"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class NAC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.NAC"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class NP_type_constituent_NP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.NP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class NX(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.NX"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class PARN(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PARN"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class PP_type_constituent_PP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class PRN(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PRN"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class PRP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PRP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class PRT_type_constituent_PRT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PRT"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class QP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.QP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class ROOT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.ROOT"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class RRC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.RRC"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class S(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.S"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class SBAR(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.SBAR"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class SBARQ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.SBARQ"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class SINV(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.SINV"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class SQ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.SQ"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class UCP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.UCP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class VP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.VP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class WHADJP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.WHADJP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class WHADVP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.WHADVP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class WHNP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.WHNP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class WHPP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.WHPP"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class X_type_constituent_X(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.X"
    children: Optional[list[UimaValue]] = None
    constituentType: Optional[str] = None
    parent: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.ADJP": ADJP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.ADVP": ADVP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.CONJP": CONJP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.Constituent": Constituent,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.FRAG": FRAG,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.INTJ": INTJ_type_constituent_INTJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.LST": LST_type_constituent_LST,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.NAC": NAC,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.NP": NP_type_constituent_NP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.NX": NX,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PARN": PARN,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PP": PP_type_constituent_PP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PRN": PRN,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PRP": PRP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.PRT": PRT_type_constituent_PRT,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.QP": QP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.ROOT": ROOT,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.RRC": RRC,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.S": S,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.SBAR": SBAR,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.SBARQ": SBARQ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.SINV": SINV,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.SQ": SQ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.UCP": UCP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.VP": VP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.WHADJP": WHADJP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.WHADVP": WHADVP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.WHNP": WHNP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.WHPP": WHPP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.constituent.X": X_type_constituent_X,
}

__all__ = [
    "ADJP",
    "ADVP",
    "CONJP",
    "Constituent",
    "FRAG",
    "INTJ_type_constituent_INTJ",
    "LST_type_constituent_LST",
    "NAC",
    "NP_type_constituent_NP",
    "NX",
    "PARN",
    "PP_type_constituent_PP",
    "PRN",
    "PRP",
    "PRT_type_constituent_PRT",
    "QP",
    "ROOT",
    "RRC",
    "S",
    "SBAR",
    "SBARQ",
    "SINV",
    "SQ",
    "UCP",
    "VP",
    "WHADJP",
    "WHADVP",
    "WHNP",
    "WHPP",
    "X_type_constituent_X",
    "UIMA_TYPE_TO_CLASS",
]
