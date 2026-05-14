from __future__ import annotations

from collections.abc import AsyncIterator

import hashlib
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
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import Taxon

BINOMIAL_PATTERN = re.compile(r"\b([A-Z][a-z]{2,})\s+([a-z]{2,})\b")


class TaxoNERDAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"example": "duui-taxonerd migration"}),
        descriptor=AnnotatorDescriptor(
            name="taxonerd-msgpack-lua",
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
                types={"Taxon": ["org.texttechnologylab.annotation.type.Taxon"]},
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemTaxoNERD.xml",
        parameters_schema={
            "linking": {
                "type": "string",
                "default": "gbif_backbone",
                "description": "TaxoNERD linker name.",
            },
            "threshold": {
                "type": "number",
                "default": 0.7,
                "description": "TaxoNERD threshold.",
            },
            "model": {
                "type": "string",
                "default": "en_ner_eco_md",
                "description": "TaxoNERD model.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @log_errors(recovery_suggestion="Check the incoming sofa text and TaxoNERD parameters.")
    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        logger = get_event_logger_or_none()
        text = sofa_text_value(doc.sofa) or ""
        linking = str(doc.parameters.get("linking") or "gbif_backbone")
        threshold = float(doc.parameters.get("threshold") or 0.7)
        model = str(doc.parameters.get("model") or "en_ner_eco_md")
        if logger:
            await logger.info(
                "TaxoNERD processing started",
                {"characters": len(text), "linking": linking, "threshold": threshold, "model": model},
            )
            await logger.debug(
                "TaxoNERD regex scan configured",
                {"pattern": BINOMIAL_PATTERN.pattern, "parameters": dict(doc.parameters)},
            )

        matches = 0
        for match in BINOMIAL_PATTERN.finditer(text):
            matches += 1
            mention = match.group(0)
            identifier = hashlib.sha1(f"{linking}:{mention}".encode("utf-8")).hexdigest()[:16]
            yield Taxon(
                        begin=match.start(),
                        end=match.end(),
                        value=mention,
                        identifier=identifier,
                        features={
                            "linking": linking,
                            "confidence": threshold,
                            "model": model,
                        },
            )

        elapsed_ms = int((time() - started) * 1000)
        if logger:
            await logger.metric("processing", "taxonerd_taxon_matches", matches, "count", elapsed_ms)
            await logger.info(
                "TaxoNERD processing completed",
                {"matches": matches, "elapsed_ms": elapsed_ms},
            )

        yield AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName=model,
                modelVersion="heuristic-1",
        )
        yield DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} heuristic TaxoNERD-compatible extraction",
        )


app = create_app(TaxoNERDAnnotator, request_adapter=AsyncChunkedRequestAdapter())
