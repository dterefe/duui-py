"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Act_Action_Activity(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Act_Action_Activity"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Animal_Fauna(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Animal_Fauna"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class AnnotationNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.AnnotationNode"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class Archaea(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Archaea"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class ArgEdge(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgEdge"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class ArgEdgeLeft(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgEdgeLeft"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class ArgEdgeRight(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgEdgeRight"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class ArgNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgNode"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    create: Optional[int] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None

class ArgTextSegment(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgTextSegment"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    create: Optional[int] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None

class ArgType(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgType"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    conclusion: Optional[list[UimaValue]] = None
    create: Optional[int] = None
    data: Optional[list[UimaValue]] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    mode: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None

class ArgTypeAnd(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgTypeAnd"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    conclusion: Optional[list[UimaValue]] = None
    create: Optional[int] = None
    data: Optional[list[UimaValue]] = None
    data2: Optional[list[UimaValue]] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    mode: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None

class ArgTypeDirect(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgTypeDirect"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    conclusion: Optional[list[UimaValue]] = None
    create: Optional[int] = None
    data: Optional[list[UimaValue]] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    mode: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None

class ArgTypeOr(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgTypeOr"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    conclusion: Optional[list[UimaValue]] = None
    create: Optional[int] = None
    data: Optional[list[UimaValue]] = None
    data2: Optional[list[UimaValue]] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    mode: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None

class ArgTypeUnless(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ArgTypeUnless"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    conclusion: Optional[list[UimaValue]] = None
    counterRebuttal: Optional[list[UimaValue]] = None
    create: Optional[int] = None
    data: Optional[list[UimaValue]] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    mode: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    rebuttal: Optional[list[UimaValue]] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None

class Artifact(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Artifact"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Attribute_annotation_type_Attribute(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Attribute"
    Id: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class Attribute_Property(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Attribute_Property"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Audio(Annotation):
    type: str = "org.texttechnologylab.annotation.type.Audio"
    mimetype: Optional[str] = None
    src: Optional[str] = None

class AudioSentence(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.AudioSentence"
    timeEnd: Optional[float] = None
    timeStart: Optional[float] = None

class AudioToken(Annotation):
    type: str = "org.texttechnologylab.annotation.type.AudioToken"
    timeEnd: Optional[float] = None
    timeStart: Optional[float] = None
    value: Optional[str] = None

class Bacteria(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Bacteria"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class BioContext(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.BioContext"
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Body_Corpus(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Body_Corpus"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Chromista(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Chromista"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Cognition_Ideation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Cognition_Ideation"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Color_annotation_type_Color(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Color"
    Id: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None
    value: Optional[int] = None

class Comment_annotation_type_Comment(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Comment"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    reference: Optional[UimaValue] = None
    user: Optional[str] = None

class Communication(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Communication"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Coordinate(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Coordinate"
    x: Optional[int] = None
    y: Optional[int] = None

class Edge(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Edge"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class Endpoint(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Endpoint"
    Id: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    node: Optional[UimaValue] = None
    user: Optional[str] = None

class Event_Happening(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Event_Happening"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Feeling_Emotion(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Feeling_Emotion"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Fingerprint(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Fingerprint"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    reference: Optional[UimaValue] = None
    user: Optional[str] = None

class Food(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Food"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Frame(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Frame"
    timeEnd: Optional[float] = None
    timeStart: Optional[float] = None

class Fungi(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Fungi"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Graph(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Graph"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edges: Optional[list[UimaValue]] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    nodes: Optional[list[UimaValue]] = None
    user: Optional[str] = None

class GraphBase(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.GraphBase"
    Id: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class Group_Collection(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Group_Collection"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Habitat(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Habitat"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Hyperedge(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Hyperedge"
    Id: Optional[str] = None
    create: Optional[int] = None
    endpoints: Optional[list[UimaValue]] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class Image(Annotation):
    type: str = "org.texttechnologylab.annotation.type.Image"
    height: Optional[int] = None
    mimetype: Optional[str] = None
    src: Optional[str] = None
    width: Optional[int] = None

class ImageWithCaptions(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.ImageWithCaptions"
    captionLanguage: Optional[str] = None
    captions: Optional[list[UimaValue]] = None
    height: Optional[int] = None
    mimetype: Optional[str] = None
    src: Optional[str] = None
    width: Optional[int] = None

class KnowledgeEntry_annotation_type_KnowledgeEntry(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.KnowledgeEntry"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    identifier: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    parentEntity: Optional[str] = None
    reference: Optional[str] = None
    source: Optional[str] = None
    user: Optional[str] = None

class LayerImage(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.LayerImage"
    height: Optional[int] = None
    index: Optional[int] = None
    mimetype: Optional[str] = None
    posX: Optional[int] = None
    posY: Optional[int] = None
    src: Optional[str] = None
    width: Optional[int] = None

class Lichen(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Lichen"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Location_Place(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Location_Place"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Morphology(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Morphology"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Motive(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Motive"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class MultimediaElement(Annotation):
    type: str = "org.texttechnologylab.annotation.type.MultimediaElement"
    timeEnd: Optional[float] = None
    timeStart: Optional[float] = None

class NaturalObject(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.NaturalObject"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class NaturalPhenomenon(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.NaturalPhenomenon"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Node(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Node"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class Other(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Other"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Person_HumanBeing(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Person_HumanBeing"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Plant_Flora(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Plant_Flora"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Possession_Property(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Possession_Property"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Process(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Process"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class PropEdge(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.PropEdge"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    graphSource: Optional[str] = None
    graphTarget: Optional[str] = None
    label: Optional[str] = None
    mode: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class PropGraphNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.PropGraphNode"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    create: Optional[int] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    lemma: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    pos: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    x2: Optional[str] = None
    y: Optional[str] = None
    y2: Optional[str] = None

class PropNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.PropNode"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    create: Optional[int] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    lemma: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    pos: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    x2: Optional[str] = None
    y: Optional[str] = None
    y2: Optional[str] = None

class PropRootNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.PropRootNode"
    Id: Optional[str] = None
    arguments: Optional[list[str]] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    create: Optional[int] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    lemma: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    pos: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    x2: Optional[str] = None
    y: Optional[str] = None
    y2: Optional[str] = None

class PropTextNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.PropTextNode"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    color: Optional[str] = None
    create: Optional[int] = None
    end: Optional[str] = None
    graphId: Optional[str] = None
    label: Optional[str] = None
    lemma: Optional[str] = None
    modified: Optional[int] = None
    nodeId: Optional[str] = None
    pos: Optional[str] = None
    reference: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    x: Optional[str] = None
    x2: Optional[str] = None
    y: Optional[str] = None
    y2: Optional[str] = None

class Protozoa(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Protozoa"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Quantity_Amount(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Quantity_Amount"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class QuickAnnoUnit(Annotation):
    type: str = "org.texttechnologylab.annotation.type.QuickAnnoUnit"
    combined: Optional[bool] = None
    origin: Optional[UimaValue] = None
    pos: Optional[str] = None

class QuickTreeMultiSpanNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.QuickTreeMultiSpanNode"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    children: Optional[list[UimaValue]] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    parent: Optional[UimaValue] = None
    user: Optional[str] = None

class QuickTreeNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.QuickTreeNode"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    children: Optional[list[UimaValue]] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    parent: Optional[UimaValue] = None
    user: Optional[str] = None

class Relation_annotation_type_Relation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Relation"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class RelationDescription(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.RelationDescription"
    Id: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    name: Optional[str] = None
    relationtype: Optional[str] = None
    user: Optional[str] = None

class RelationSet(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.RelationSet"
    relations: Optional[list[UimaValue]] = None

class Reproduction(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Reproduction"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Shape(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Shape"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Society(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Society"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Speaker_annotation_type_Speaker(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Speaker"
    value: Optional[str] = None

class Speech_annotation_type_Speech(Annotation):
    type: str = "org.texttechnologylab.annotation.type.Speech"
    speaker: Optional[UimaValue] = None

class State_Condition(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.State_Condition"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class SubImage(Annotation):
    type: str = "org.texttechnologylab.annotation.type.SubImage"
    coordinates: Optional[list[UimaValue]] = None
    parent: Optional[UimaValue] = None

class SubImageWithCaptions(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.SubImageWithCaptions"
    captionLanguage: Optional[str] = None
    captions: Optional[list[UimaValue]] = None
    coordinates: Optional[list[UimaValue]] = None
    parent: Optional[UimaValue] = None

class Substance_annotation_type_Substance(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Substance"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Taxon(Annotation):
    type: str = "org.texttechnologylab.annotation.type.Taxon"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class TextElement(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.TextElement"
    Id: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None
    value: Optional[UimaValue] = None

Taxon_annotation_type_Taxon = Taxon

class TextTechnologyEntity(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.TextTechnologyEntity"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[str] = None
    create: Optional[int] = None
    end: Optional[str] = None
    knowledgeEntries: Optional[list[UimaValue]] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    pos: Optional[str] = None
    subvalue: Optional[str] = None
    user: Optional[str] = None
    value: Optional[str] = None

class TextTechnologyKnowledgeEdge(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.TextTechnologyKnowledgeEdge"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    linktype: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class TexttechnologyNamedEntity(Annotation):
    type: str = "org.texttechnologylab.annotation.type.TexttechnologyNamedEntity"
    belongsTo: Optional[UimaValue] = None
    knowledgeEntries: Optional[list[str]] = None
    subvalue: Optional[str] = None
    value: Optional[str] = None
    wikidataID: Optional[str] = None
    wikipediaID: Optional[str] = None

class Time_annotation_type_Time(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Time"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class TimeEdge(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.TimeEdge"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    mode: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class TimeInnerNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.TimeInnerNode"
    Id: Optional[str] = None
    additionalvalue: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    depth: Optional[int] = None
    edges: Optional[list[UimaValue]] = None
    end: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    nodes: Optional[list[UimaValue]] = None
    subvalue: Optional[str] = None
    user: Optional[str] = None
    value: Optional[str] = None
    x: Optional[int] = None
    xPos: Optional[int] = None
    y: Optional[int] = None

class TimeNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.TimeNode"
    Id: Optional[str] = None
    additionalvalue: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    depth: Optional[int] = None
    edges: Optional[list[UimaValue]] = None
    end: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    nodes: Optional[list[UimaValue]] = None
    subvalue: Optional[str] = None
    user: Optional[str] = None
    value: Optional[str] = None
    x: Optional[int] = None
    xPos: Optional[int] = None
    y: Optional[int] = None

class TreeAnnotationNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.TreeAnnotationNode"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    children: Optional[list[UimaValue]] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    parent: Optional[UimaValue] = None
    user: Optional[str] = None

class TreeNode(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.TreeNode"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    children: Optional[list[UimaValue]] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    parent: Optional[UimaValue] = None
    user: Optional[str] = None

class Unknown(Annotation):
    type: str = "org.texttechnologylab.annotation.type.Unknown"
    value: Optional[str] = None

class Vehicle(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Vehicle"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class Video_annotation_type_Video(Annotation):
    type: str = "org.texttechnologylab.annotation.type.Video"
    fps: Optional[float] = None
    length: Optional[float] = None
    mimetype: Optional[str] = None
    src: Optional[str] = None

class VideoToken(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.VideoToken"
    timeEnd: Optional[float] = None
    timeStart: Optional[float] = None

class Viruses(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Viruses"
    identifier: Optional[str] = None
    metaphor: Optional[bool] = None
    metonym: Optional[bool] = None
    specific: Optional[bool] = None
    value: Optional[str] = None

class WebImage(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.WebImage"
    height: Optional[int] = None
    mimetype: Optional[str] = None
    posX: Optional[int] = None
    posY: Optional[int] = None
    src: Optional[str] = None
    width: Optional[int] = None

class Weight(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.Weight"
    Id: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None
    value: Optional[float] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.type.Act_Action_Activity": Act_Action_Activity,
    "org.texttechnologylab.annotation.type.Animal_Fauna": Animal_Fauna,
    "org.texttechnologylab.annotation.type.AnnotationNode": AnnotationNode,
    "org.texttechnologylab.annotation.type.Archaea": Archaea,
    "org.texttechnologylab.annotation.type.ArgEdge": ArgEdge,
    "org.texttechnologylab.annotation.type.ArgEdgeLeft": ArgEdgeLeft,
    "org.texttechnologylab.annotation.type.ArgEdgeRight": ArgEdgeRight,
    "org.texttechnologylab.annotation.type.ArgNode": ArgNode,
    "org.texttechnologylab.annotation.type.ArgTextSegment": ArgTextSegment,
    "org.texttechnologylab.annotation.type.ArgType": ArgType,
    "org.texttechnologylab.annotation.type.ArgTypeAnd": ArgTypeAnd,
    "org.texttechnologylab.annotation.type.ArgTypeDirect": ArgTypeDirect,
    "org.texttechnologylab.annotation.type.ArgTypeOr": ArgTypeOr,
    "org.texttechnologylab.annotation.type.ArgTypeUnless": ArgTypeUnless,
    "org.texttechnologylab.annotation.type.Artifact": Artifact,
    "org.texttechnologylab.annotation.type.Attribute": Attribute_annotation_type_Attribute,
    "org.texttechnologylab.annotation.type.Attribute_Property": Attribute_Property,
    "org.texttechnologylab.annotation.type.Audio": Audio,
    "org.texttechnologylab.annotation.type.AudioSentence": AudioSentence,
    "org.texttechnologylab.annotation.type.AudioToken": AudioToken,
    "org.texttechnologylab.annotation.type.Bacteria": Bacteria,
    "org.texttechnologylab.annotation.type.BioContext": BioContext,
    "org.texttechnologylab.annotation.type.Body_Corpus": Body_Corpus,
    "org.texttechnologylab.annotation.type.Chromista": Chromista,
    "org.texttechnologylab.annotation.type.Cognition_Ideation": Cognition_Ideation,
    "org.texttechnologylab.annotation.type.Color": Color_annotation_type_Color,
    "org.texttechnologylab.annotation.type.Comment": Comment_annotation_type_Comment,
    "org.texttechnologylab.annotation.type.Communication": Communication,
    "org.texttechnologylab.annotation.type.Coordinate": Coordinate,
    "org.texttechnologylab.annotation.type.Edge": Edge,
    "org.texttechnologylab.annotation.type.Endpoint": Endpoint,
    "org.texttechnologylab.annotation.type.Event_Happening": Event_Happening,
    "org.texttechnologylab.annotation.type.Feeling_Emotion": Feeling_Emotion,
    "org.texttechnologylab.annotation.type.Fingerprint": Fingerprint,
    "org.texttechnologylab.annotation.type.Food": Food,
    "org.texttechnologylab.annotation.type.Frame": Frame,
    "org.texttechnologylab.annotation.type.Fungi": Fungi,
    "org.texttechnologylab.annotation.type.Graph": Graph,
    "org.texttechnologylab.annotation.type.GraphBase": GraphBase,
    "org.texttechnologylab.annotation.type.Group_Collection": Group_Collection,
    "org.texttechnologylab.annotation.type.Habitat": Habitat,
    "org.texttechnologylab.annotation.type.Hyperedge": Hyperedge,
    "org.texttechnologylab.annotation.type.Image": Image,
    "org.texttechnologylab.annotation.type.ImageWithCaptions": ImageWithCaptions,
    "org.texttechnologylab.annotation.type.KnowledgeEntry": KnowledgeEntry_annotation_type_KnowledgeEntry,
    "org.texttechnologylab.annotation.type.LayerImage": LayerImage,
    "org.texttechnologylab.annotation.type.Lichen": Lichen,
    "org.texttechnologylab.annotation.type.Location_Place": Location_Place,
    "org.texttechnologylab.annotation.type.Morphology": Morphology,
    "org.texttechnologylab.annotation.type.Motive": Motive,
    "org.texttechnologylab.annotation.type.MultimediaElement": MultimediaElement,
    "org.texttechnologylab.annotation.type.NaturalObject": NaturalObject,
    "org.texttechnologylab.annotation.type.NaturalPhenomenon": NaturalPhenomenon,
    "org.texttechnologylab.annotation.type.Node": Node,
    "org.texttechnologylab.annotation.type.Other": Other,
    "org.texttechnologylab.annotation.type.Person_HumanBeing": Person_HumanBeing,
    "org.texttechnologylab.annotation.type.Plant_Flora": Plant_Flora,
    "org.texttechnologylab.annotation.type.Possession_Property": Possession_Property,
    "org.texttechnologylab.annotation.type.Process": Process,
    "org.texttechnologylab.annotation.type.PropEdge": PropEdge,
    "org.texttechnologylab.annotation.type.PropGraphNode": PropGraphNode,
    "org.texttechnologylab.annotation.type.PropNode": PropNode,
    "org.texttechnologylab.annotation.type.PropRootNode": PropRootNode,
    "org.texttechnologylab.annotation.type.PropTextNode": PropTextNode,
    "org.texttechnologylab.annotation.type.Protozoa": Protozoa,
    "org.texttechnologylab.annotation.type.Quantity_Amount": Quantity_Amount,
    "org.texttechnologylab.annotation.type.QuickAnnoUnit": QuickAnnoUnit,
    "org.texttechnologylab.annotation.type.QuickTreeMultiSpanNode": QuickTreeMultiSpanNode,
    "org.texttechnologylab.annotation.type.QuickTreeNode": QuickTreeNode,
    "org.texttechnologylab.annotation.type.Relation": Relation_annotation_type_Relation,
    "org.texttechnologylab.annotation.type.RelationDescription": RelationDescription,
    "org.texttechnologylab.annotation.type.RelationSet": RelationSet,
    "org.texttechnologylab.annotation.type.Reproduction": Reproduction,
    "org.texttechnologylab.annotation.type.Shape": Shape,
    "org.texttechnologylab.annotation.type.Society": Society,
    "org.texttechnologylab.annotation.type.Speaker": Speaker_annotation_type_Speaker,
    "org.texttechnologylab.annotation.type.Speech": Speech_annotation_type_Speech,
    "org.texttechnologylab.annotation.type.State_Condition": State_Condition,
    "org.texttechnologylab.annotation.type.SubImage": SubImage,
    "org.texttechnologylab.annotation.type.SubImageWithCaptions": SubImageWithCaptions,
    "org.texttechnologylab.annotation.type.Substance": Substance_annotation_type_Substance,
    "org.texttechnologylab.annotation.type.Taxon": Taxon,
    "org.texttechnologylab.annotation.type.TextElement": TextElement,
    "org.texttechnologylab.annotation.type.TextTechnologyEntity": TextTechnologyEntity,
    "org.texttechnologylab.annotation.type.TextTechnologyKnowledgeEdge": TextTechnologyKnowledgeEdge,
    "org.texttechnologylab.annotation.type.TexttechnologyNamedEntity": TexttechnologyNamedEntity,
    "org.texttechnologylab.annotation.type.Time": Time_annotation_type_Time,
    "org.texttechnologylab.annotation.type.TimeEdge": TimeEdge,
    "org.texttechnologylab.annotation.type.TimeInnerNode": TimeInnerNode,
    "org.texttechnologylab.annotation.type.TimeNode": TimeNode,
    "org.texttechnologylab.annotation.type.TreeAnnotationNode": TreeAnnotationNode,
    "org.texttechnologylab.annotation.type.TreeNode": TreeNode,
    "org.texttechnologylab.annotation.type.Unknown": Unknown,
    "org.texttechnologylab.annotation.type.Vehicle": Vehicle,
    "org.texttechnologylab.annotation.type.Video": Video_annotation_type_Video,
    "org.texttechnologylab.annotation.type.VideoToken": VideoToken,
    "org.texttechnologylab.annotation.type.Viruses": Viruses,
    "org.texttechnologylab.annotation.type.WebImage": WebImage,
    "org.texttechnologylab.annotation.type.Weight": Weight,
}

__all__ = [
    "Act_Action_Activity",
    "Animal_Fauna",
    "AnnotationNode",
    "Archaea",
    "ArgEdge",
    "ArgEdgeLeft",
    "ArgEdgeRight",
    "ArgNode",
    "ArgTextSegment",
    "ArgType",
    "ArgTypeAnd",
    "ArgTypeDirect",
    "ArgTypeOr",
    "ArgTypeUnless",
    "Artifact",
    "Attribute_annotation_type_Attribute",
    "Attribute_Property",
    "Audio",
    "AudioSentence",
    "AudioToken",
    "Bacteria",
    "BioContext",
    "Body_Corpus",
    "Chromista",
    "Cognition_Ideation",
    "Color_annotation_type_Color",
    "Comment_annotation_type_Comment",
    "Communication",
    "Coordinate",
    "Edge",
    "Endpoint",
    "Event_Happening",
    "Feeling_Emotion",
    "Fingerprint",
    "Food",
    "Frame",
    "Fungi",
    "Graph",
    "GraphBase",
    "Group_Collection",
    "Habitat",
    "Hyperedge",
    "Image",
    "ImageWithCaptions",
    "KnowledgeEntry_annotation_type_KnowledgeEntry",
    "LayerImage",
    "Lichen",
    "Location_Place",
    "Morphology",
    "Motive",
    "MultimediaElement",
    "NaturalObject",
    "NaturalPhenomenon",
    "Node",
    "Other",
    "Person_HumanBeing",
    "Plant_Flora",
    "Possession_Property",
    "Process",
    "PropEdge",
    "PropGraphNode",
    "PropNode",
    "PropRootNode",
    "PropTextNode",
    "Protozoa",
    "Quantity_Amount",
    "QuickAnnoUnit",
    "QuickTreeMultiSpanNode",
    "QuickTreeNode",
    "Relation_annotation_type_Relation",
    "RelationDescription",
    "RelationSet",
    "Reproduction",
    "Shape",
    "Society",
    "Speaker_annotation_type_Speaker",
    "Speech_annotation_type_Speech",
    "State_Condition",
    "SubImage",
    "SubImageWithCaptions",
    "Substance_annotation_type_Substance",
    "Taxon",
    "TextElement",
    "TextTechnologyEntity",
    "TextTechnologyKnowledgeEdge",
    "TexttechnologyNamedEntity",
    "Time_annotation_type_Time",
    "TimeEdge",
    "TimeInnerNode",
    "TimeNode",
    "TreeAnnotationNode",
    "TreeNode",
    "Unknown",
    "Vehicle",
    "Video_annotation_type_Video",
    "VideoToken",
    "Viruses",
    "WebImage",
    "Weight",
    "UIMA_TYPE_TO_CLASS",
]
