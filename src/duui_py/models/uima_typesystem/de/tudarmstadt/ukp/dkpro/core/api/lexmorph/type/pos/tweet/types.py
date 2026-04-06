"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class AT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.AT"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class DM(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.DM"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class EMO(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.EMO"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class HASH(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.HASH"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class INT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.INT"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class NNV(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.NNV"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class NPV(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.NPV"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_AT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_AT"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_DM(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_DM"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_EMO(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_EMO"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_HASH(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_HASH"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_INT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_INT"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_NNV(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_NNV"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_NPV(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_NPV"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class POS_URL(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_URL"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

class URL(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.URL"
    PosValue: Optional[str] = None
    coarseValue: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.AT": AT,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.DM": DM,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.EMO": EMO,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.HASH": HASH,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.INT": INT,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.NNV": NNV,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.NPV": NPV,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_AT": POS_AT,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_DM": POS_DM,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_EMO": POS_EMO,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_HASH": POS_HASH,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_INT": POS_INT,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_NNV": POS_NNV,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_NPV": POS_NPV,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.POS_URL": POS_URL,
    "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.tweet.URL": URL,
}

__all__ = [
    "AT",
    "DM",
    "EMO",
    "HASH",
    "INT",
    "NNV",
    "NPV",
    "POS_AT",
    "POS_DM",
    "POS_EMO",
    "POS_HASH",
    "POS_INT",
    "POS_NNV",
    "POS_NPV",
    "POS_URL",
    "URL",
    "UIMA_TYPE_TO_CLASS",
]
