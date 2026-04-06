"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.ocr."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class OCRBlock(Annotation):
    type: str = "org.texttechnologylab.annotation.ocr.OCRBlock"
    blockName: Optional[str] = None
    blockType: Optional[str] = None
    bottom: Optional[int] = None
    left: Optional[int] = None
    right: Optional[int] = None
    top: Optional[int] = None
    valid: Optional[bool] = None

class OCRDocument(Annotation):
    type: str = "org.texttechnologylab.annotation.ocr.OCRDocument"
    documentname: Optional[str] = None

class OCRFormat(Annotation):
    type: str = "org.texttechnologylab.annotation.ocr.OCRFormat"
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

class OCRLine(Annotation):
    type: str = "org.texttechnologylab.annotation.ocr.OCRLine"
    baseline: Optional[int] = None
    bottom: Optional[int] = None
    format: Optional[str] = None
    left: Optional[int] = None
    right: Optional[int] = None
    top: Optional[int] = None

class OCRPage(Annotation):
    type: str = "org.texttechnologylab.annotation.ocr.OCRPage"
    height: Optional[int] = None
    pageId: Optional[str] = None
    pageNumber: Optional[int] = None
    resolution: Optional[int] = None
    uri: Optional[str] = None
    width: Optional[int] = None

class OCRParagraph(Annotation):
    type: str = "org.texttechnologylab.annotation.ocr.OCRParagraph"
    align: Optional[str] = None
    leftIndent: Optional[int] = None
    lineSpacing: Optional[int] = None
    rightIndent: Optional[int] = None
    startIndent: Optional[int] = None

class OCRToken(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ocr.OCRToken"
    containsHyphen: Optional[bool] = None
    form: Optional[UimaValue] = None
    id: Optional[str] = None
    isWordFromDictionary: Optional[bool] = None
    isWordNormal: Optional[bool] = None
    isWordNumeric: Optional[bool] = None
    lemma: Optional[UimaValue] = None
    morph: Optional[UimaValue] = None
    order: Optional[int] = None
    parent: Optional[UimaValue] = None
    pos: Optional[UimaValue] = None
    stem: Optional[UimaValue] = None
    subTokenList: Optional[list[str]] = None
    suspiciousChars: Optional[int] = None
    syntacticFunction: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.ocr.OCRBlock": OCRBlock,
    "org.texttechnologylab.annotation.ocr.OCRDocument": OCRDocument,
    "org.texttechnologylab.annotation.ocr.OCRFormat": OCRFormat,
    "org.texttechnologylab.annotation.ocr.OCRLine": OCRLine,
    "org.texttechnologylab.annotation.ocr.OCRPage": OCRPage,
    "org.texttechnologylab.annotation.ocr.OCRParagraph": OCRParagraph,
    "org.texttechnologylab.annotation.ocr.OCRToken": OCRToken,
}

__all__ = [
    "OCRBlock",
    "OCRDocument",
    "OCRFormat",
    "OCRLine",
    "OCRPage",
    "OCRParagraph",
    "OCRToken",
    "UIMA_TYPE_TO_CLASS",
]
