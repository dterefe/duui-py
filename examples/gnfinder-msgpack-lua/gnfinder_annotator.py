from __future__ import annotations

from collections.abc import AsyncIterator

import re
from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.metrics import metrics
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    AnnotatorMetaData,
    DocumentModification,
    Domain,
    DomainSpec,
    IODescriptor,
    V1RequestEnvelope,
)
from duui_py.models.uima import sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.biofid.gnfinder.types import GNFinderTaxon, VerifiedTaxon

BINOMIAL_PATTERN = re.compile(r"\b([A-Z][a-z]{2,})\s+([a-z]{2,})\b")


class GNFinderAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"example": "duui-gnfinder migration"}),
        descriptor=AnnotatorDescriptor(
            name="gnfinder-msgpack-lua",
            version="1.0.0",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                )
            ),
            output=IODescriptor(
                types={
                    "Taxon": [
                        "org.texttechnologylab.annotation.biofid.gnfinder.Taxon",
                        "org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon",
                    ]
                },
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemGNFinder.xml",
        parameters_schema={
            "lang": {
                "type": "string",
                "default": "detect",
                "description": "Language hint for name detection.",
            },
            "verify": {
                "type": "boolean",
                "default": True,
                "description": "Keep parity with GNFinder verify parameter.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        lang = str(doc.parameters.get("lang") or "detect")
        verify = bool(doc.parameters.get("verify", True))

        matches = 0
        for m in BINOMIAL_PATTERN.finditer(text):
            matches += 1
            value = m.group(0)
            cardinality = 2
            odds = 0.75 if verify else 0.5
            if verify:
                yield VerifiedTaxon(
                        begin=m.start(),
                        end=m.end(),
                        value=value,
                        cardinality=cardinality,
                        oddsLog10=odds,
                        matchedName=value,
                        matchedCanonicalSimple=value,
                        matchedCanonicalFull=value,
                        currentName=value,
                        dataSourceId=0,
                        recordId=f"heuristic-{m.start()}-{m.end()}",
                        sortScore=odds,
                        editDistance=0,
                )
            else:
                yield GNFinderTaxon(
                        begin=m.start(),
                        end=m.end(),
                        value=value,
                        cardinality=cardinality,
                        oddsLog10=odds,
                )

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("gnfinder_taxon_matches", matches, lang=lang, verify=str(verify).lower())
        await metrics.timing("gnfinder_processing_ms", elapsed_ms)

        yield AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName="regex-binomial",
                modelVersion="1",
        )
        yield DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} heuristic GNFinder-compatible extraction",
        )


app = create_app(GNFinderAnnotator, request_adapter=AsyncChunkedRequestAdapter())
