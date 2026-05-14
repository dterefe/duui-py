from __future__ import annotations

from collections.abc import AsyncIterator

import re
from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.logging import get_event_logger_or_none, log_errors
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

    @log_errors(recovery_suggestion="Check the incoming sofa text and GNFinder parameters.")
    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        logger = get_event_logger_or_none()
        text = sofa_text_value(doc.sofa) or ""
        lang = str(doc.parameters.get("lang") or "detect")
        verify = bool(doc.parameters.get("verify", True))

        if logger:
            await logger.info(
                "GNFinder processing started",
                {"characters": len(text), "lang": lang, "verify": verify},
            )
            await logger.debug(
                "GNFinder regex scan configured",
                {"pattern": BINOMIAL_PATTERN.pattern, "parameters": dict(doc.parameters)},
            )

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
        if logger:
            await logger.metric("processing", "gnfinder_taxon_matches", matches, "count", elapsed_ms)
            await logger.info(
                "GNFinder processing completed",
                {"matches": matches, "elapsed_ms": elapsed_ms},
            )

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
