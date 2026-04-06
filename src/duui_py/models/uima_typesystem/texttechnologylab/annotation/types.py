"""Auto-generated UIMA models for namespace: texttechnologylab.annotation."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class AbstractNamedEntity(Annotation):
    type: str = "org.texttechnologylab.annotation.AbstractNamedEntity"
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class AnnotationBracket(Annotation):
    type: str = "org.texttechnologylab.annotation.AnnotationBracket"
    pass

class AnnotationComment(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.AnnotationComment"
    key: Optional[str] = None
    reference: Optional[UimaValue] = None
    value: Optional[str] = None

class AnnotationPerspective(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.AnnotationPerspective"
    name: Optional[str] = None
    reference: Optional[UimaValue] = None

class AnnotatorMetaData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.AnnotatorMetaData"
    modelName: Optional[str] = None
    modelVersion: Optional[str] = None
    name: Optional[str] = None
    reference: Optional[UimaValue] = None
    version: Optional[str] = None

class AnomalySpellingMeta(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.AnomalySpellingMeta"
    GoodQuality: Optional[float] = None
    ModelName: Optional[str] = None
    PercentRight: Optional[float] = None
    PercentRightWithoutSkipped: Optional[float] = None
    PercentUnknown: Optional[float] = None
    PercentUnknownWithoutSkipped: Optional[float] = None
    PercentWrong: Optional[float] = None
    PercentWrongWithoutSkipped: Optional[float] = None
    Quality: Optional[float] = None
    RightWords: Optional[int] = None
    SkippedWords: Optional[int] = None
    UnknownQuality: Optional[float] = None
    UnknownWords: Optional[int] = None
    WrongWords: Optional[int] = None

class AnomlySpelling(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.AnomlySpelling"
    ModelName: Optional[str] = None
    SpellingType: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    suggestions: Optional[list[UimaValue]] = None

class Argument(Annotation):
    type: str = "org.texttechnologylab.annotation.Argument"
    Arguments: Optional[list[UimaValue]] = None
    model: Optional[UimaValue] = None
    reason: Optional[str] = None
    topic: Optional[str] = None

class ArgumentExtraction(Annotation):
    type: str = "org.texttechnologylab.annotation.ArgumentExtraction"
    model: Optional[UimaValue] = None
    reason: Optional[str] = None
    value: Optional[str] = None

class Attribution(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Attribution"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class BertTopic(Annotation):
    type: str = "org.texttechnologylab.annotation.BertTopic"
    Topics: Optional[list[UimaValue]] = None
    model: Optional[UimaValue] = None

class Caption(Annotation):
    type: str = "org.texttechnologylab.annotation.Caption"
    mediaType: Optional[str] = None
    value: Optional[str] = None

class Claim(Annotation):
    type: str = "org.texttechnologylab.annotation.Claim"
    Facts: Optional[list[UimaValue]] = None
    value: Optional[str] = None

class Color(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Color"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    rgb: Optional[str] = None
    user: Optional[str] = None

class Complexity(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Complexity"
    Kind: Optional[str] = None
    Output: Optional[float] = None
    SentenceI: Optional[UimaValue] = None
    SentenceJ: Optional[UimaValue] = None
    model: Optional[UimaValue] = None

class Coreference(Annotation):
    type: str = "org.texttechnologylab.annotation.Coreference"
    link: Optional[UimaValue] = None

class CorpusAnnotation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.CorpusAnnotation"
    author: Optional[str] = None
    comment: Optional[str] = None
    corpusName: Optional[str] = None
    corpusUrl: Optional[str] = None
    license: Optional[str] = None

class DocumentAnnotation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.DocumentAnnotation"
    author: Optional[str] = None
    dateDay: Optional[int] = None
    dateMonth: Optional[int] = None
    dateYear: Optional[int] = None
    place: Optional[str] = None
    publisher: Optional[str] = None
    subtitle: Optional[str] = None
    timestamp: Optional[int] = None

class DocumentModification(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.DocumentModification"
    comment: Optional[str] = None
    timestamp: Optional[int] = None
    user: Optional[str] = None

class Emotion_texttechnologylab_annotation_Emotion(Annotation):
    type: str = "org.texttechnologylab.annotation.Emotion"
    Emotions: Optional[list[UimaValue]] = None
    model: Optional[UimaValue] = None

class Entailment(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Entailment"
    contradiction: Optional[float] = None
    entailment: Optional[float] = None
    model: Optional[UimaValue] = None
    reference: Optional[UimaValue] = None

class EntailmentGPT(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.EntailmentGPT"
    Confidence: Optional[float] = None
    Label: Optional[str] = None
    Reason: Optional[str] = None
    model: Optional[UimaValue] = None
    reference: Optional[UimaValue] = None

class EntailmentSentence(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.EntailmentSentence"
    hypothesis: Optional[UimaValue] = None
    premise: Optional[UimaValue] = None

class EssayScore(Annotation):
    type: str = "org.texttechnologylab.annotation.EssayScore"
    InputAnswer: Optional[UimaValue] = None
    InputQuestion: Optional[UimaValue] = None
    InputScene: Optional[UimaValue] = None
    Name: Optional[str] = None
    Reason: Optional[str] = None
    Value: Optional[float] = None

class Fact(Annotation):
    type: str = "org.texttechnologylab.annotation.Fact"
    Claims: Optional[list[UimaValue]] = None
    value: Optional[str] = None

class FactChecking(Annotation):
    type: str = "org.texttechnologylab.annotation.FactChecking"
    Claim: Optional[UimaValue] = None
    Fact: Optional[UimaValue] = None
    consistency: Optional[float] = None
    model: Optional[UimaValue] = None

class GNMetaData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.GNMetaData"
    Lang: Optional[str] = None
    Source: Optional[str] = None
    date: Optional[str] = None
    version: Optional[str] = None
    wihUniqueNames: Optional[bool] = None
    withAllMatches: Optional[bool] = None
    withAmbiguousNames: Optional[bool] = None
    withBayes: Optional[bool] = None
    withOddsAdjustment: Optional[bool] = None
    withSources: Optional[str] = None

class Genre(Annotation):
    type: str = "org.texttechnologylab.annotation.Genre"
    Genres: Optional[list[UimaValue]] = None
    model: Optional[UimaValue] = None

class GeoNamesEntity(Annotation):
    type: str = "org.texttechnologylab.annotation.GeoNamesEntity"
    id: Optional[int] = None
    mainclass: Optional[str] = None
    subclass: Optional[str] = None

class Hate(Annotation):
    type: str = "org.texttechnologylab.annotation.Hate"
    Hate: Optional[float] = None
    NonHate: Optional[float] = None
    model: Optional[UimaValue] = None

class Hypothesis(Annotation):
    type: str = "org.texttechnologylab.annotation.Hypothesis"
    Stances: Optional[list[UimaValue]] = None

class L2SCA(Annotation):
    type: str = "org.texttechnologylab.annotation.L2SCA"
    Code: Optional[str] = None
    Measure: Optional[str] = None
    Value: Optional[float] = None
    definition: Optional[str] = None
    model: Optional[UimaValue] = None
    typeName: Optional[str] = None
    typeNumber: Optional[int] = None

class LLMMetric(Annotation):
    type: str = "org.texttechnologylab.annotation.LLMMetric"
    KeyName: Optional[str] = None
    Value: Optional[float] = None
    definition: Optional[str] = None
    model: Optional[UimaValue] = None

class Language_texttechnologylab_annotation_Language(Annotation):
    type: str = "org.texttechnologylab.annotation.Language"
    score: Optional[float] = None
    value: Optional[str] = None

class LanguageModel(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.LanguageModel"
    Language: Optional[UimaValue] = None
    Model: Optional[UimaValue] = None

class MetaData(Annotation):
    type: str = "org.texttechnologylab.annotation.MetaData"
    Lang: Optional[str] = None
    Source: Optional[str] = None

class ModelAnnotation(Annotation):
    type: str = "org.texttechnologylab.annotation.ModelAnnotation"
    ModelReference: Optional[UimaValue] = None

class NamedEntity_texttechnologylab_annotation_NamedEntity(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.NamedEntity"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class OffensiveSpeech(Annotation):
    type: str = "org.texttechnologylab.annotation.OffensiveSpeech"
    Offensives: Optional[list[UimaValue]] = None
    model: Optional[UimaValue] = None

class Orientation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Orientation"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class OrientationEdge(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.OrientationEdge"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class Paraphrase(Annotation):
    type: str = "org.texttechnologylab.annotation.Paraphrase"
    value: Optional[str] = None

class Readability(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Readability"
    TextReadabilities: Optional[list[UimaValue]] = None
    model: Optional[UimaValue] = None

class ReadabilityAdvance(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.ReadabilityAdvance"
    GroupName: Optional[str] = None
    TextReadabilities: Optional[list[UimaValue]] = None
    model: Optional[UimaValue] = None

class Sarcasm(Annotation):
    type: str = "org.texttechnologylab.annotation.Sarcasm"
    NonSarcasm: Optional[float] = None
    Sarcasm: Optional[float] = None
    model: Optional[UimaValue] = None

class SemanticSource(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.SemanticSource"
    comment: Optional[str] = None
    searchResult: Optional[str] = None
    source: Optional[str] = None
    value: Optional[str] = None

class SentenceComparison(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.SentenceComparison"
    SentenceI: Optional[UimaValue] = None
    SentenceJ: Optional[UimaValue] = None

class SentimentBert(Annotation):
    type: str = "org.texttechnologylab.annotation.SentimentBert"
    probabilityNegative: Optional[float] = None
    probabilityNeutral: Optional[float] = None
    probabilityPositive: Optional[float] = None
    sentiment: Optional[int] = None

class SentimentModel(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.SentimentModel"
    model: Optional[UimaValue] = None
    probabilityNegative: Optional[float] = None
    probabilityNeutral: Optional[float] = None
    probabilityPositive: Optional[float] = None
    sentiment: Optional[int] = None

class SharedData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.SharedData"
    value: Optional[str] = None

class SpacyAnnotatorMetaData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.SpacyAnnotatorMetaData"
    modelLang: Optional[str] = None
    modelName: Optional[str] = None
    modelSpacyGitVersion: Optional[str] = None
    modelSpacyVersion: Optional[str] = None
    modelVersion: Optional[str] = None
    name: Optional[str] = None
    reference: Optional[UimaValue] = None
    spacyVersion: Optional[str] = None
    version: Optional[str] = None

class Stance(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Stance"
    Neutral: Optional[float] = None
    Oppose: Optional[float] = None
    Reference: Optional[UimaValue] = None
    Support: Optional[float] = None
    model: Optional[UimaValue] = None

class StanceBase(Annotation):
    type: str = "org.texttechnologylab.annotation.StanceBase"
    Reference: Optional[UimaValue] = None
    model: Optional[UimaValue] = None

class StanceGPT(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.StanceGPT"
    Confidence: Optional[float] = None
    Label: Optional[str] = None
    Reason: Optional[str] = None
    Reference: Optional[UimaValue] = None
    model: Optional[UimaValue] = None

class StanceSentence(Annotation):
    type: str = "org.texttechnologylab.annotation.StanceSentence"
    pass

class SubcatMatch(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.SubcatMatch"
    context: Optional[str] = None
    elements: Optional[list[UimaValue]] = None
    status: Optional[str] = None

class Summary_texttechnologylab_annotation_Summary(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Summary"
    Reference: Optional[UimaValue] = None
    Summary: Optional[str] = None
    model: Optional[UimaValue] = None

class TAscore(Annotation):
    type: str = "org.texttechnologylab.annotation.TAscore"
    group: Optional[str] = None
    name: Optional[str] = None
    ref: Optional[UimaValue] = None
    score: Optional[float] = None

class Temporal(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Temporal"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class TextAbstract(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.TextAbstract"
    value: Optional[str] = None

class Topic(Annotation):
    type: str = "org.texttechnologylab.annotation.Topic"
    Topics: Optional[list[UimaValue]] = None
    model: Optional[UimaValue] = None

class TopicValue(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.TopicValue"
    probability: Optional[float] = None
    value: Optional[str] = None

class TopicValueBase(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.TopicValueBase"
    value: Optional[str] = None
    words: Optional[list[UimaValue]] = None

class TopicValueBaseWithScore(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.TopicValueBaseWithScore"
    score: Optional[float] = None
    value: Optional[str] = None
    words: Optional[list[UimaValue]] = None

class TopicWord(Annotation):
    type: str = "org.texttechnologylab.annotation.TopicWord"
    probability: Optional[float] = None
    topic: Optional[UimaValue] = None
    word: Optional[str] = None

class Toxic(Annotation):
    type: str = "org.texttechnologylab.annotation.Toxic"
    NonToxic: Optional[float] = None
    Toxic: Optional[float] = None
    model: Optional[UimaValue] = None

class Translation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Translation"
    Reference: Optional[UimaValue] = None
    context: Optional[str] = None
    model: Optional[UimaValue] = None
    score: Optional[float] = None
    value: Optional[str] = None

class UnifiedTopic(Annotation):
    type: str = "org.texttechnologylab.annotation.UnifiedTopic"
    Topics: Optional[list[UimaValue]] = None
    metadata: Optional[UimaValue] = None

class Vector(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Vector"
    w: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.AbstractNamedEntity": AbstractNamedEntity,
    "org.texttechnologylab.annotation.AnnotationBracket": AnnotationBracket,
    "org.texttechnologylab.annotation.AnnotationComment": AnnotationComment,
    "org.texttechnologylab.annotation.AnnotationPerspective": AnnotationPerspective,
    "org.texttechnologylab.annotation.AnnotatorMetaData": AnnotatorMetaData,
    "org.texttechnologylab.annotation.AnomalySpellingMeta": AnomalySpellingMeta,
    "org.texttechnologylab.annotation.AnomlySpelling": AnomlySpelling,
    "org.texttechnologylab.annotation.Argument": Argument,
    "org.texttechnologylab.annotation.ArgumentExtraction": ArgumentExtraction,
    "org.texttechnologylab.annotation.Attribution": Attribution,
    "org.texttechnologylab.annotation.BertTopic": BertTopic,
    "org.texttechnologylab.annotation.Caption": Caption,
    "org.texttechnologylab.annotation.Claim": Claim,
    "org.texttechnologylab.annotation.Color": Color,
    "org.texttechnologylab.annotation.Complexity": Complexity,
    "org.texttechnologylab.annotation.Coreference": Coreference,
    "org.texttechnologylab.annotation.CorpusAnnotation": CorpusAnnotation,
    "org.texttechnologylab.annotation.DocumentAnnotation": DocumentAnnotation,
    "org.texttechnologylab.annotation.DocumentModification": DocumentModification,
    "org.texttechnologylab.annotation.Emotion": Emotion_texttechnologylab_annotation_Emotion,
    "org.texttechnologylab.annotation.Entailment": Entailment,
    "org.texttechnologylab.annotation.EntailmentGPT": EntailmentGPT,
    "org.texttechnologylab.annotation.EntailmentSentence": EntailmentSentence,
    "org.texttechnologylab.annotation.EssayScore": EssayScore,
    "org.texttechnologylab.annotation.Fact": Fact,
    "org.texttechnologylab.annotation.FactChecking": FactChecking,
    "org.texttechnologylab.annotation.GNMetaData": GNMetaData,
    "org.texttechnologylab.annotation.Genre": Genre,
    "org.texttechnologylab.annotation.GeoNamesEntity": GeoNamesEntity,
    "org.texttechnologylab.annotation.Hate": Hate,
    "org.texttechnologylab.annotation.Hypothesis": Hypothesis,
    "org.texttechnologylab.annotation.L2SCA": L2SCA,
    "org.texttechnologylab.annotation.LLMMetric": LLMMetric,
    "org.texttechnologylab.annotation.Language": Language_texttechnologylab_annotation_Language,
    "org.texttechnologylab.annotation.LanguageModel": LanguageModel,
    "org.texttechnologylab.annotation.MetaData": MetaData,
    "org.texttechnologylab.annotation.ModelAnnotation": ModelAnnotation,
    "org.texttechnologylab.annotation.NamedEntity": NamedEntity_texttechnologylab_annotation_NamedEntity,
    "org.texttechnologylab.annotation.OffensiveSpeech": OffensiveSpeech,
    "org.texttechnologylab.annotation.Orientation": Orientation,
    "org.texttechnologylab.annotation.OrientationEdge": OrientationEdge,
    "org.texttechnologylab.annotation.Paraphrase": Paraphrase,
    "org.texttechnologylab.annotation.Readability": Readability,
    "org.texttechnologylab.annotation.ReadabilityAdvance": ReadabilityAdvance,
    "org.texttechnologylab.annotation.Sarcasm": Sarcasm,
    "org.texttechnologylab.annotation.SemanticSource": SemanticSource,
    "org.texttechnologylab.annotation.SentenceComparison": SentenceComparison,
    "org.texttechnologylab.annotation.SentimentBert": SentimentBert,
    "org.texttechnologylab.annotation.SentimentModel": SentimentModel,
    "org.texttechnologylab.annotation.SharedData": SharedData,
    "org.texttechnologylab.annotation.SpacyAnnotatorMetaData": SpacyAnnotatorMetaData,
    "org.texttechnologylab.annotation.Stance": Stance,
    "org.texttechnologylab.annotation.StanceBase": StanceBase,
    "org.texttechnologylab.annotation.StanceGPT": StanceGPT,
    "org.texttechnologylab.annotation.StanceSentence": StanceSentence,
    "org.texttechnologylab.annotation.SubcatMatch": SubcatMatch,
    "org.texttechnologylab.annotation.Summary": Summary_texttechnologylab_annotation_Summary,
    "org.texttechnologylab.annotation.TAscore": TAscore,
    "org.texttechnologylab.annotation.Temporal": Temporal,
    "org.texttechnologylab.annotation.TextAbstract": TextAbstract,
    "org.texttechnologylab.annotation.Topic": Topic,
    "org.texttechnologylab.annotation.TopicValue": TopicValue,
    "org.texttechnologylab.annotation.TopicValueBase": TopicValueBase,
    "org.texttechnologylab.annotation.TopicValueBaseWithScore": TopicValueBaseWithScore,
    "org.texttechnologylab.annotation.TopicWord": TopicWord,
    "org.texttechnologylab.annotation.Toxic": Toxic,
    "org.texttechnologylab.annotation.Translation": Translation,
    "org.texttechnologylab.annotation.UnifiedTopic": UnifiedTopic,
    "org.texttechnologylab.annotation.Vector": Vector,
}

__all__ = [
    "AbstractNamedEntity",
    "AnnotationBracket",
    "AnnotationComment",
    "AnnotationPerspective",
    "AnnotatorMetaData",
    "AnomalySpellingMeta",
    "AnomlySpelling",
    "Argument",
    "ArgumentExtraction",
    "Attribution",
    "BertTopic",
    "Caption",
    "Claim",
    "Color",
    "Complexity",
    "Coreference",
    "CorpusAnnotation",
    "DocumentAnnotation",
    "DocumentModification",
    "Emotion_texttechnologylab_annotation_Emotion",
    "Entailment",
    "EntailmentGPT",
    "EntailmentSentence",
    "EssayScore",
    "Fact",
    "FactChecking",
    "GNMetaData",
    "Genre",
    "GeoNamesEntity",
    "Hate",
    "Hypothesis",
    "L2SCA",
    "LLMMetric",
    "Language_texttechnologylab_annotation_Language",
    "LanguageModel",
    "MetaData",
    "ModelAnnotation",
    "NamedEntity_texttechnologylab_annotation_NamedEntity",
    "OffensiveSpeech",
    "Orientation",
    "OrientationEdge",
    "Paraphrase",
    "Readability",
    "ReadabilityAdvance",
    "Sarcasm",
    "SemanticSource",
    "SentenceComparison",
    "SentimentBert",
    "SentimentModel",
    "SharedData",
    "SpacyAnnotatorMetaData",
    "Stance",
    "StanceBase",
    "StanceGPT",
    "StanceSentence",
    "SubcatMatch",
    "Summary_texttechnologylab_annotation_Summary",
    "TAscore",
    "Temporal",
    "TextAbstract",
    "Topic",
    "TopicValue",
    "TopicValueBase",
    "TopicValueBaseWithScore",
    "TopicWord",
    "Toxic",
    "Translation",
    "UnifiedTopic",
    "Vector",
    "UIMA_TYPE_TO_CLASS",
]
