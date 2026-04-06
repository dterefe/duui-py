"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.model."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class EssayScoreLLM(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.model.EssayScoreLLM"
    AdditionalInformation: Optional[str] = None
    Contents: Optional[str] = None
    ModelName: Optional[str] = None
    Response: Optional[str] = None
    ScoreReference: Optional[UimaValue] = None
    model: Optional[UimaValue] = None

class EssayScoreModel(Annotation):
    type: str = "org.texttechnologylab.annotation.model.EssayScoreModel"
    ScoreReference: Optional[UimaValue] = None
    model: Optional[UimaValue] = None

class FactCheckingMetaData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.model.FactCheckingMetaData"
    DependeciesVersion: Optional[list[str]] = None
    Lang: Optional[str] = None
    ModelName: Optional[str] = None
    ModelVersion: Optional[str] = None
    Source: Optional[str] = None

class HuggingfaceMetaData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.model.HuggingfaceMetaData"
    DependeciesVersion: Optional[list[str]] = None
    HuggingfaceVersion: Optional[str] = None
    Lang: Optional[str] = None
    ModelName: Optional[str] = None
    ModelVersion: Optional[str] = None
    Source: Optional[str] = None

class MetaData_annotation_model_MetaData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.model.MetaData"
    Lang: Optional[str] = None
    ModelName: Optional[str] = None
    ModelVersion: Optional[str] = None
    Source: Optional[str] = None

class SpacyMetaData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.model.SpacyMetaData"
    Lang: Optional[str] = None
    ModelName: Optional[str] = None
    ModelSpacyGitVersion: Optional[str] = None
    ModelVersion: Optional[str] = None
    Source: Optional[str] = None
    SpacyVersion: Optional[str] = None

class TrainedModelBase(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.model.TrainedModelBase"
    modelBase64: Optional[str] = None

class TrainedModelDetail(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.model.TrainedModelDetail"
    accuracy: Optional[float] = None
    epochs: Optional[int] = None
    f1Macro: Optional[float] = None
    f1Weighted: Optional[float] = None
    framework: Optional[str] = None
    learningRate: Optional[float] = None
    loss: Optional[float] = None
    modelBase64: Optional[str] = None
    modelName: Optional[str] = None
    modelVersion: Optional[str] = None
    precisionMacro: Optional[float] = None
    precisionWeighted: Optional[float] = None
    recallMacro: Optional[float] = None
    recallWeighted: Optional[float] = None
    testAccuracy: Optional[float] = None
    testLoss: Optional[float] = None
    testSamples: Optional[int] = None
    trainSamples: Optional[int] = None
    valAccuracy: Optional[float] = None
    valLoss: Optional[float] = None
    valSamples: Optional[int] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.model.EssayScoreLLM": EssayScoreLLM,
    "org.texttechnologylab.annotation.model.EssayScoreModel": EssayScoreModel,
    "org.texttechnologylab.annotation.model.FactCheckingMetaData": FactCheckingMetaData,
    "org.texttechnologylab.annotation.model.HuggingfaceMetaData": HuggingfaceMetaData,
    "org.texttechnologylab.annotation.model.MetaData": MetaData_annotation_model_MetaData,
    "org.texttechnologylab.annotation.model.SpacyMetaData": SpacyMetaData,
    "org.texttechnologylab.annotation.model.TrainedModelBase": TrainedModelBase,
    "org.texttechnologylab.annotation.model.TrainedModelDetail": TrainedModelDetail,
}

__all__ = [
    "EssayScoreLLM",
    "EssayScoreModel",
    "FactCheckingMetaData",
    "HuggingfaceMetaData",
    "MetaData_annotation_model_MetaData",
    "SpacyMetaData",
    "TrainedModelBase",
    "TrainedModelDetail",
    "UIMA_TYPE_TO_CLASS",
]
