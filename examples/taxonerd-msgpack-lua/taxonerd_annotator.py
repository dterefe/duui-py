from __future__ import annotations

import hashlib
import re
from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import AnnotatorMetaData, DocumentModification, V1RequestEnvelope, DuuiResult
from duui_py.models.uima import Annotation, sofa_text_value

TAXON_TYPE = "org.texttechnologylab.annotation.type.Taxon"
BINOMIAL_PATTERN = re.compile(r"\\b([A-Z][a-z]{2,})\\s+([a-z]{2,})\\b")


class Taxon(Annotation):
    type: str = TAXON_TYPE


class TaxoNERDAnnotator(DuuiAnnotator[V1RequestEnvelope, DuuiResult]):
    config_path = "annotator_config.json"

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> DuuiResult:
        text = sofa_text_value(doc.sofa) or ""
        linking = str(doc.parameters.get("linking") or "gbif_backbone")
        threshold = float(doc.parameters.get("threshold") or 0.7)
        model = str(doc.parameters.get("model") or "en_ner_eco_md")

        annotations: list[Taxon] = []
        for match in BINOMIAL_PATTERN.finditer(text):
            mention = match.group(0)
            identifier = hashlib.sha1(f"{linking}:{mention}".encode("utf-8")).hexdigest()[:16]
            annotations.append(
                Taxon(
                    begin=match.start(),
                    end=match.end(),
                    features={
                        "value": mention,
                        "identifier": identifier,
                        "linking": linking,
                        "confidence": threshold,
                        "model": model,
                    },
                )
            )

        return DuuiResult(
            annotations=annotations,
            meta=AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName=model,
                modelVersion="heuristic-1",
            ),
            modification_meta=DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} heuristic TaxoNERD-compatible extraction",
            ),
        )


app = create_app(TaxoNERDAnnotator)
