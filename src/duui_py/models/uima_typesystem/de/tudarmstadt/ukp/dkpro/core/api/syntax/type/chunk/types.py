"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ADJC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.ADJC"
    chunkValue: Optional[str] = None

class ADVC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.ADVC"
    chunkValue: Optional[str] = None

class CONCJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.CONCJ"
    chunkValue: Optional[str] = None

class Chunk(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.Chunk"
    chunkValue: Optional[str] = None

class INTJ_type_chunk_INTJ(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.INTJ"
    chunkValue: Optional[str] = None

class LST(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.LST"
    chunkValue: Optional[str] = None

class NC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.NC"
    chunkValue: Optional[str] = None

class O_type_chunk_O(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.O"
    chunkValue: Optional[str] = None

class PC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.PC"
    chunkValue: Optional[str] = None

class PRT_type_chunk_PRT(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.PRT"
    chunkValue: Optional[str] = None

class VC(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.VC"
    chunkValue: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.ADJC": ADJC,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.ADVC": ADVC,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.CONCJ": CONCJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.Chunk": Chunk,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.INTJ": INTJ_type_chunk_INTJ,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.LST": LST,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.NC": NC,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.O": O_type_chunk_O,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.PC": PC,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.PRT": PRT_type_chunk_PRT,
    "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.chunk.VC": VC,
}

__all__ = [
    "ADJC",
    "ADVC",
    "CONCJ",
    "Chunk",
    "INTJ_type_chunk_INTJ",
    "LST",
    "NC",
    "O_type_chunk_O",
    "PC",
    "PRT_type_chunk_PRT",
    "VC",
    "UIMA_TYPE_TO_CLASS",
]
