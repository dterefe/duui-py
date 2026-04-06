"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ADJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.ADJ"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class ADP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.ADP"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class ADV(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.ADV"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class ART(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.ART"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class AUX(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.AUX"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class CARD(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.CARD"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class CONJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.CONJ"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class DET(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.DET"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class INTJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.INTJ"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class N(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.N"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class NN(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.NN"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class NOUN(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.NOUN"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class NP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.NP"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class NUM(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.NUM"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class O(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.O"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class PART(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PART"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_ADJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_ADJ"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_ADP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_ADP"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_ADV(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_ADV"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_AUX(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_AUX"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_CONJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_CONJ"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_DET(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_DET"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_INTJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_INTJ"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_NOUN(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_NOUN"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_NUM(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_NUM"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_PART(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_PART"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_PRON(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_PRON"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_PROPN(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_PROPN"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_PUNCT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_PUNCT"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_SCONJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_SCONJ"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_SYM(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_SYM"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_VERB(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_VERB"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_X(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_X"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class PP(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PP"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class PR(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PR"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class PRON(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PRON"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class PROPN(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PROPN"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class PRT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PRT"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class PUNC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PUNC"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class PUNCT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PUNCT"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class SCONJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.SCONJ"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class SYM(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.SYM"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class V(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.V"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class VERB(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.VERB"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class X(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.X"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.ADJ": ADJ,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.ADP": ADP,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.ADV": ADV,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.ART": ART,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.AUX": AUX,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.CARD": CARD,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.CONJ": CONJ,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.DET": DET,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.INTJ": INTJ,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.N": N,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.NN": NN,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.NOUN": NOUN,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.NP": NP,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.NUM": NUM,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.O": O,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PART": PART,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS": POS,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_ADJ": POS_ADJ,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_ADP": POS_ADP,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_ADV": POS_ADV,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_AUX": POS_AUX,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_CONJ": POS_CONJ,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_DET": POS_DET,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_INTJ": POS_INTJ,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_NOUN": POS_NOUN,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_NUM": POS_NUM,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_PART": POS_PART,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_PRON": POS_PRON,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_PROPN": POS_PROPN,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_PUNCT": POS_PUNCT,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_SCONJ": POS_SCONJ,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_SYM": POS_SYM,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_VERB": POS_VERB,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS_X": POS_X,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PP": PP,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PR": PR,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PRON": PRON,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PROPN": PROPN,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PRT": PRT,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PUNC": PUNC,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.PUNCT": PUNCT,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.SCONJ": SCONJ,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.SYM": SYM,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.V": V,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.VERB": VERB,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.X": X,
}

__all__ = [
    "ADJ",
    "ADP",
    "ADV",
    "ART",
    "AUX",
    "CARD",
    "CONJ",
    "DET",
    "INTJ",
    "N",
    "NN",
    "NOUN",
    "NP",
    "NUM",
    "O",
    "PART",
    "POS",
    "POS_ADJ",
    "POS_ADP",
    "POS_ADV",
    "POS_AUX",
    "POS_CONJ",
    "POS_DET",
    "POS_INTJ",
    "POS_NOUN",
    "POS_NUM",
    "POS_PART",
    "POS_PRON",
    "POS_PROPN",
    "POS_PUNCT",
    "POS_SCONJ",
    "POS_SYM",
    "POS_VERB",
    "POS_X",
    "PP",
    "PR",
    "PRON",
    "PROPN",
    "PRT",
    "PUNC",
    "PUNCT",
    "SCONJ",
    "SYM",
    "V",
    "VERB",
    "X",
    "UIMA_TYPE_TO_CLASS",
]
