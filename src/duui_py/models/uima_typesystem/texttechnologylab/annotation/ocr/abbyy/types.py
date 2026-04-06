"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.ocr.abbyy."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Block(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.Block"
    blockName: Optional[str] = None
    blockType: Optional[UimaValue] = None
    bottom: Optional[int] = None
    divType: Optional[str] = None
    id: Optional[str] = None
    left: Optional[int] = None
    right: Optional[int] = None
    top: Optional[int] = None

class BlockType(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.BlockType"
    pass

class Document_ocr_abbyy_Document(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.Document"
    divType: Optional[str] = None
    documentName: Optional[str] = None
    id: Optional[str] = None
    languages: Optional[str] = None
    mainLanguage: Optional[str] = None
    pagesCount: Optional[int] = None
    producer: Optional[str] = None
    version: Optional[str] = None

class Format(Annotation):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.Format"
    bold: Optional[bool] = None
    ff: Optional[str] = None
    fs: Optional[float] = None
    italic: Optional[bool] = None
    lang: Optional[str] = None
    smallcaps: Optional[bool] = None
    strikeout: Optional[bool] = None
    subscript: Optional[bool] = None
    superscript: Optional[bool] = None
    underline: Optional[bool] = None

class Line_ocr_abbyy_Line(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.Line"
    baseline: Optional[int] = None
    bottom: Optional[int] = None
    divType: Optional[str] = None
    format: Optional[UimaValue] = None
    id: Optional[str] = None
    left: Optional[int] = None
    right: Optional[int] = None
    top: Optional[int] = None

class Orientation_ocr_abbyy_Orientation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.Orientation"
    pass

class Page_ocr_abbyy_Page(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.Page"
    divType: Optional[str] = None
    height: Optional[int] = None
    id: Optional[str] = None
    index: Optional[int] = None
    pageNumber: Optional[str] = None
    resolution: Optional[int] = None
    rotation: Optional[UimaValue] = None
    uri: Optional[str] = None
    width: Optional[int] = None

class Paragraph_ocr_abbyy_Paragraph(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.Paragraph"
    alignment: Optional[UimaValue] = None
    divType: Optional[str] = None
    id: Optional[str] = None
    leftIndent: Optional[int] = None
    lineSpacing: Optional[int] = None
    rightIndent: Optional[int] = None
    startIndent: Optional[int] = None

class ParagraphAlignment(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.ParagraphAlignment"
    pass

class StructuralElement(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.StructuralElement"
    bottom: Optional[int] = None
    divType: Optional[str] = None
    id: Optional[str] = None
    left: Optional[int] = None
    right: Optional[int] = None
    top: Optional[int] = None

class Token_ocr_abbyy_Token(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.abbyy.Token"
    containsHyphen: Optional[bool] = None
    form: Optional[UimaValue] = None
    id: Optional[str] = None
    isWordFromDictionary: Optional[bool] = None
    isWordNormal: Optional[bool] = None
    isWordNumeric: Optional[bool] = None
    lemma: Optional[UimaValue] = None
    meanCharConfidence: Optional[float] = None
    minCharConfidence: Optional[int] = None
    morph: Optional[UimaValue] = None
    order: Optional[int] = None
    parent: Optional[UimaValue] = None
    pos: Optional[UimaValue] = None
    stem: Optional[UimaValue] = None
    subTokenList: Optional[list[str]] = None
    suspiciousChars: Optional[int] = None
    syntacticFunction: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.ocr.abbyy.Block": Block,
    "org.texttechnologylab.annotation.ocr.abbyy.BlockType": BlockType,
    "org.texttechnologylab.annotation.ocr.abbyy.Document": Document_ocr_abbyy_Document,
    "org.texttechnologylab.annotation.ocr.abbyy.Format": Format,
    "org.texttechnologylab.annotation.ocr.abbyy.Line": Line_ocr_abbyy_Line,
    "org.texttechnologylab.annotation.ocr.abbyy.Orientation": Orientation_ocr_abbyy_Orientation,
    "org.texttechnologylab.annotation.ocr.abbyy.Page": Page_ocr_abbyy_Page,
    "org.texttechnologylab.annotation.ocr.abbyy.Paragraph": Paragraph_ocr_abbyy_Paragraph,
    "org.texttechnologylab.annotation.ocr.abbyy.ParagraphAlignment": ParagraphAlignment,
    "org.texttechnologylab.annotation.ocr.abbyy.StructuralElement": StructuralElement,
    "org.texttechnologylab.annotation.ocr.abbyy.Token": Token_ocr_abbyy_Token,
}

__all__ = [
    "Block",
    "BlockType",
    "Document_ocr_abbyy_Document",
    "Format",
    "Line_ocr_abbyy_Line",
    "Orientation_ocr_abbyy_Orientation",
    "Page_ocr_abbyy_Page",
    "Paragraph_ocr_abbyy_Paragraph",
    "ParagraphAlignment",
    "StructuralElement",
    "Token_ocr_abbyy_Token",
    "UIMA_TYPE_TO_CLASS",
]
