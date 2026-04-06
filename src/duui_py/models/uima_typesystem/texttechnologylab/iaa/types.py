"""Auto-generated UIMA models for namespace: texttechnologylab.iaa."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Agreement(Annotation):
    type: str = "org.texttechnologylab.iaa.Agreement"
    agreementMeasure: Optional[str] = None
    agreementValue: Optional[float] = None

class AgreementContainer(Annotation):
    type: str = "org.texttechnologylab.iaa.AgreementContainer"
    agreementMeasure: Optional[str] = None
    categoryAgreementValues: Optional[list[float]] = None
    categoryCounts: Optional[list[int]] = None
    categoryNames: Optional[list[str]] = None
    categorySpecificAgreementValues: Optional[list[str]] = None
    overallAgreementValue: Optional[float] = None

class AgreementValue(FeatureStructure):
    type: str = "org.texttechnologylab.iaa.AgreementValue"
    agreementLabel: Optional[str] = None
    agreementUnits: Optional[int] = None
    agreementValue: Optional[float] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.iaa.Agreement": Agreement,
    "org.texttechnologylab.iaa.AgreementContainer": AgreementContainer,
    "org.texttechnologylab.iaa.AgreementValue": AgreementValue,
}

__all__ = [
    "Agreement",
    "AgreementContainer",
    "AgreementValue",
    "UIMA_TYPE_TO_CLASS",
]
