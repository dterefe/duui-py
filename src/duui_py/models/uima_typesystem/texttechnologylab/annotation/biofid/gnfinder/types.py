"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.biofid.gnfinder."""

from __future__ import annotations

from typing import Optional
from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class MatchType(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.gnfinder.MatchType"
    pass

class GNFinderMetaData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.gnfinder.MetaData"
    date: Optional[str] = None
    language: Optional[str] = None
    other: Optional[list[UimaValue]] = None
    references: Optional[list[UimaValue]] = None
    version: Optional[str] = None

class MetaDataKeyValue(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.gnfinder.MetaDataKeyValue"
    key: Optional[str] = None
    value: Optional[str] = None

class OddsDetails(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.gnfinder.OddsDetails"
    feature: Optional[str] = None
    odds: Optional[float] = None

class GNFinderTaxon(Annotation):
    type: str = "org.texttechnologylab.annotation.biofid.gnfinder.Taxon"
    cardinality: Optional[int] = None
    identifier: Optional[str] = None
    oddsDetails: Optional[list[UimaValue]] = None
    oddsLog10: Optional[float] = None
    value: Optional[str] = None

class TaxonomicStatus(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.gnfinder.TaxonomicStatus"
    pass

class VerifiedTaxon(GNFinderTaxon):
    type: str = "org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon"
    currentName: Optional[str] = None
    dataSourceId: Optional[int] = None
    editDistance: Optional[int] = None
    globalId: Optional[str] = None
    localId: Optional[str] = None
    matchType: Optional[UimaValue] = None
    matchedCanonicalFull: Optional[str] = None
    matchedCanonicalSimple: Optional[str] = None
    matchedName: Optional[str] = None
    outlink: Optional[str] = None
    recordId: Optional[str] = None
    sortScore: Optional[float] = None
    taxonomicStatus: Optional[UimaValue] = None

MetaData_biofid_gnfinder_MetaData = GNFinderMetaData
Taxon_biofid_gnfinder_Taxon = GNFinderTaxon

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.biofid.gnfinder.MatchType": MatchType,
    "org.texttechnologylab.annotation.biofid.gnfinder.MetaData": GNFinderMetaData,
    "org.texttechnologylab.annotation.biofid.gnfinder.MetaDataKeyValue": MetaDataKeyValue,
    "org.texttechnologylab.annotation.biofid.gnfinder.OddsDetails": OddsDetails,
    "org.texttechnologylab.annotation.biofid.gnfinder.Taxon": GNFinderTaxon,
    "org.texttechnologylab.annotation.biofid.gnfinder.TaxonomicStatus": TaxonomicStatus,
    "org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon": VerifiedTaxon,
}

__all__ = [
    "MatchType",
    "GNFinderMetaData",
    "MetaDataKeyValue",
    "OddsDetails",
    "GNFinderTaxon",
    "TaxonomicStatus",
    "VerifiedTaxon",
    "UIMA_TYPE_TO_CLASS",
]
