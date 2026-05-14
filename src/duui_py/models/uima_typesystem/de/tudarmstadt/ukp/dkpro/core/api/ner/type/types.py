"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.ner.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Animal(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Animal"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Cardinal(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Cardinal"
    identifier: Optional[str] = None
    value: Optional[str] = None

class ContactInfo(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.ContactInfo"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Date(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Date"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Disease(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Disease"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Event(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Event"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Fac(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Fac"
    identifier: Optional[str] = None
    value: Optional[str] = None

class FacDesc(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.FacDesc"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Game(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Game"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Gpe(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Gpe"
    identifier: Optional[str] = None
    value: Optional[str] = None

class GpeDesc(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.GpeDesc"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Language(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Language"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Law(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Law"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Location(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Location"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Money(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Money"
    identifier: Optional[str] = None
    value: Optional[str] = None

class NamedEntity(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Nationality(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Nationality"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Norp(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Norp"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Ordinal(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Ordinal"
    identifier: Optional[str] = None
    value: Optional[str] = None

class OrgDesc(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.OrgDesc"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Organization(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Organization"
    identifier: Optional[str] = None
    value: Optional[str] = None

class PerDesc(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.PerDesc"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Percent(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Percent"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Person(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Person"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Plant(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Plant"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Product(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Product"
    identifier: Optional[str] = None
    value: Optional[str] = None

class ProductDesc(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.ProductDesc"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Quantity(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Quantity"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Substance(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Substance"
    identifier: Optional[str] = None
    value: Optional[str] = None

class Time(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Time"
    identifier: Optional[str] = None
    value: Optional[str] = None

class WorkOfArt(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.WorkOfArt"
    identifier: Optional[str] = None
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Animal": Animal,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Cardinal": Cardinal,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.ContactInfo": ContactInfo,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Date": Date,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Disease": Disease,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Event": Event,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Fac": Fac,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.FacDesc": FacDesc,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Game": Game,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Gpe": Gpe,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.GpeDesc": GpeDesc,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Language": Language,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Law": Law,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Location": Location,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Money": Money,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity": NamedEntity,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Nationality": Nationality,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Norp": Norp,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Ordinal": Ordinal,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.OrgDesc": OrgDesc,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Organization": Organization,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.PerDesc": PerDesc,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Percent": Percent,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Person": Person,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Plant": Plant,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Product": Product,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.ProductDesc": ProductDesc,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Quantity": Quantity,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Substance": Substance,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.Time": Time,
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.WorkOfArt": WorkOfArt,
}

__all__ = [
    "Animal",
    "Cardinal",
    "ContactInfo",
    "Date",
    "Disease",
    "Event",
    "Fac",
    "FacDesc",
    "Game",
    "Gpe",
    "GpeDesc",
    "Language",
    "Law",
    "Location",
    "Money",
    "NamedEntity",
    "Nationality",
    "Norp",
    "Ordinal",
    "OrgDesc",
    "Organization",
    "PerDesc",
    "Percent",
    "Person",
    "Plant",
    "Product",
    "ProductDesc",
    "Quantity",
    "Substance",
    "Time",
    "WorkOfArt",
    "UIMA_TYPE_TO_CLASS",
]
