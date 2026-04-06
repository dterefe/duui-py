"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.segmentation.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Compound(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Compound"
    splits: Optional[list[UimaValue]] = None

class CompoundPart(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.CompoundPart"
    splits: Optional[list[UimaValue]] = None

class Div(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Div"
    divType: Optional[str] = None
    id: Optional[str] = None

class Document(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Document"
    divType: Optional[str] = None
    id: Optional[str] = None

class Heading(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Heading"
    divType: Optional[str] = None
    id: Optional[str] = None

class Lemma(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"
    value: Optional[str] = None

class LexicalPhrase(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.LexicalPhrase"
    text: Optional[str] = None

class LinkingMorpheme(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.LinkingMorpheme"
    splits: Optional[list[UimaValue]] = None

class NGram(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.NGram"
    text: Optional[str] = None

class Paragraph(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph"
    divType: Optional[str] = None
    id: Optional[str] = None

class Sentence(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
    id: Optional[str] = None

class Split(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Split"
    splits: Optional[list[UimaValue]] = None

class Stem(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Stem"
    value: Optional[str] = None

class StopWord(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.StopWord"
    pass

class SurfaceForm(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.SurfaceForm"
    value: Optional[str] = None

class Token(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
    form: Optional[UimaValue] = None
    id: Optional[str] = None
    lemma: Optional[UimaValue] = None
    morph: Optional[UimaValue] = None
    order: Optional[int] = None
    parent: Optional[UimaValue] = None
    pos: Optional[UimaValue] = None
    stem: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

class TokenForm(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.TokenForm"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Compound": Compound,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.CompoundPart": CompoundPart,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Div": Div,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Document": Document,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Heading": Heading,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma": Lemma,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.LexicalPhrase": LexicalPhrase,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.LinkingMorpheme": LinkingMorpheme,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.NGram": NGram,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph": Paragraph,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence": Sentence,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Split": Split,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Stem": Stem,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.StopWord": StopWord,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.SurfaceForm": SurfaceForm,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token": Token,
    "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.TokenForm": TokenForm,
}

__all__ = [
    "Compound",
    "CompoundPart",
    "Div",
    "Document",
    "Heading",
    "Lemma",
    "LexicalPhrase",
    "LinkingMorpheme",
    "NGram",
    "Paragraph",
    "Sentence",
    "Split",
    "Stem",
    "StopWord",
    "SurfaceForm",
    "Token",
    "TokenForm",
    "UIMA_TYPE_TO_CLASS",
]
