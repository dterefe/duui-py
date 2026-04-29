from __future__ import annotations

import re
from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import AnnotatorMetaData, DocumentModification, V1RequestEnvelope, DuuiResult
from duui_py.models.uima import Annotation, sofa_text_value

GNFINDER_TAXON_TYPE = "org.texttechnologylab.annotation.biofid.gnfinder.Taxon"
BINOMIAL_PATTERN = re.compile(r"\\b([A-Z][a-z]{2,})\\s+([a-z]{2,})\\b")


class GNFinderTaxon(Annotation):
    type: str = GNFINDER_TAXON_TYPE


class GNFinderAnnotator(DuuiAnnotator[V1RequestEnvelope, DuuiResult]):
    config_path = "annotator_config.json"

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> DuuiResult:
        text = sofa_text_value(doc.sofa) or ""
        lang = str(doc.parameters.get("lang") or "detect")
        verify = bool(doc.parameters.get("verify", True))

        matches = list(BINOMIAL_PATTERN.finditer(text))
        annotations: list[GNFinderTaxon] = []
        for m in matches:
            value = m.group(0)
            cardinality = 2
            odds = 0.75 if verify else 0.5
            annotations.append(
                GNFinderTaxon(
                    begin=m.start(),
                    end=m.end(),
                    features={
                        "value": value,
                        "Cardinality": cardinality,
                        "OddsLog10": odds,
                        "Language": lang,
                        "Version": "heuristic-1",
                    },
                )
            )

        return DuuiResult(
            annotations=annotations,
            meta=AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName="regex-binomial",
                modelVersion="1",
            ),
            modification_meta=DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} heuristic GNFinder-compatible extraction",
            ),
        )


app = create_app(GNFinderAnnotator)
