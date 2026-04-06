"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ABBREV(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ABBREV"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class ACOMP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ACOMP"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class ADVCL(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ADVCL"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class ADVMOD(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ADVMOD"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class AGENT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.AGENT"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class AMOD(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.AMOD"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class APPOS(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.APPOS"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class ATTR(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ATTR"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class AUX0(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.AUX0"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class AUXPASS(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.AUXPASS"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class CC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CC"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class CCOMP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CCOMP"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class COMPLM(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.COMPLM"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class CONJ_type_dependency_CONJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CONJ"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class CONJP_type_dependency_CONJP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CONJP"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class CONJ_YET(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CONJ_YET"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class COP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.COP"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class CSUBJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CSUBJ"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class CSUBJPASS(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CSUBJPASS"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class DEP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.DEP"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class DET_type_dependency_DET(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.DET"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class DOBJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.DOBJ"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class Dependency(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class EXPL(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.EXPL"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class INFMOD(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.INFMOD"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class IOBJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.IOBJ"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class MARK(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.MARK"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class MEASURE(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.MEASURE"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class MWE(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.MWE"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class NEG(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NEG"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class NN_type_dependency_NN(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NN"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class NPADVMOD(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NPADVMOD"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class NSUBJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NSUBJ"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class NSUBJPASS(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NSUBJPASS"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class NUM_type_dependency_NUM(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NUM"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class NUMBER(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NUMBER"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PARATAXIS(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PARATAXIS"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PARTMOD(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PARTMOD"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PCOMP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PCOMP"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class POBJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.POBJ"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class POSS(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.POSS"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class POSSESSIVE(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.POSSESSIVE"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PRECONJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PRECONJ"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PRED(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PRED"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PREDET(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PREDET"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PREP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PREP"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PREPC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PREPC"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PRT_type_dependency_PRT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PRT"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PUNCT_type_dependency_PUNCT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PUNCT"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class PURPCL(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PURPCL"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class QUANTMOD(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.QUANTMOD"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class RCMOD(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.RCMOD"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class REF(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.REF"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class REL(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.REL"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class ROOT_type_dependency_ROOT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ROOT"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class TMOD(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.TMOD"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class XCOMP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.XCOMP"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

class XSUBJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.XSUBJ"
    DependencyType: Optional[str] = None
    Dependent: Optional[UimaValue] = None
    Governor: Optional[UimaValue] = None
    flavor: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ABBREV": ABBREV,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ACOMP": ACOMP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ADVCL": ADVCL,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ADVMOD": ADVMOD,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.AGENT": AGENT,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.AMOD": AMOD,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.APPOS": APPOS,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ATTR": ATTR,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.AUX0": AUX0,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.AUXPASS": AUXPASS,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CC": CC,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CCOMP": CCOMP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.COMPLM": COMPLM,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CONJ": CONJ_type_dependency_CONJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CONJP": CONJP_type_dependency_CONJP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CONJ_YET": CONJ_YET,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.COP": COP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CSUBJ": CSUBJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.CSUBJPASS": CSUBJPASS,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.DEP": DEP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.DET": DET_type_dependency_DET,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.DOBJ": DOBJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency": Dependency,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.EXPL": EXPL,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.INFMOD": INFMOD,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.IOBJ": IOBJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.MARK": MARK,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.MEASURE": MEASURE,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.MWE": MWE,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NEG": NEG,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NN": NN_type_dependency_NN,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NPADVMOD": NPADVMOD,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NSUBJ": NSUBJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NSUBJPASS": NSUBJPASS,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NUM": NUM_type_dependency_NUM,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.NUMBER": NUMBER,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PARATAXIS": PARATAXIS,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PARTMOD": PARTMOD,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PCOMP": PCOMP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.POBJ": POBJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.POSS": POSS,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.POSSESSIVE": POSSESSIVE,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PRECONJ": PRECONJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PRED": PRED,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PREDET": PREDET,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PREP": PREP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PREPC": PREPC,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PRT": PRT_type_dependency_PRT,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PUNCT": PUNCT_type_dependency_PUNCT,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.PURPCL": PURPCL,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.QUANTMOD": QUANTMOD,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.RCMOD": RCMOD,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.REF": REF,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.REL": REL,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ROOT": ROOT_type_dependency_ROOT,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.TMOD": TMOD,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.XCOMP": XCOMP,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.XSUBJ": XSUBJ,
}

__all__ = [
    "ABBREV",
    "ACOMP",
    "ADVCL",
    "ADVMOD",
    "AGENT",
    "AMOD",
    "APPOS",
    "ATTR",
    "AUX0",
    "AUXPASS",
    "CC",
    "CCOMP",
    "COMPLM",
    "CONJ_type_dependency_CONJ",
    "CONJP_type_dependency_CONJP",
    "CONJ_YET",
    "COP",
    "CSUBJ",
    "CSUBJPASS",
    "DEP",
    "DET_type_dependency_DET",
    "DOBJ",
    "Dependency",
    "EXPL",
    "INFMOD",
    "IOBJ",
    "MARK",
    "MEASURE",
    "MWE",
    "NEG",
    "NN_type_dependency_NN",
    "NPADVMOD",
    "NSUBJ",
    "NSUBJPASS",
    "NUM_type_dependency_NUM",
    "NUMBER",
    "PARATAXIS",
    "PARTMOD",
    "PCOMP",
    "POBJ",
    "POSS",
    "POSSESSIVE",
    "PRECONJ",
    "PRED",
    "PREDET",
    "PREP",
    "PREPC",
    "PRT_type_dependency_PRT",
    "PUNCT_type_dependency_PUNCT",
    "PURPCL",
    "QUANTMOD",
    "RCMOD",
    "REF",
    "REL",
    "ROOT_type_dependency_ROOT",
    "TMOD",
    "XCOMP",
    "XSUBJ",
    "UIMA_TYPE_TO_CLASS",
]
