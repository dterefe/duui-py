from __future__ import annotations

from collections.abc import AsyncIterator

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
from duui_py.models.uima import FeatureStructure, sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import AnnotationComment, Argument


class ArgumentAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"example": "duui-argument migration"}),
        descriptor=AnnotatorDescriptor(
            name="argument-msgpack-lua",
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
                    "Argument": ["org.texttechnologylab.annotation.Argument"],
                    "AnnotationComment": ["org.texttechnologylab.annotation.AnnotationComment"],
                },
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemArgument.xml",
        parameters_schema={
            "topic": {
                "type": "string",
                "default": "general",
                "description": "Topic used for argument scoring.",
            },
            "selection_types": {
                "type": "string",
                "description": "Comma-separated annotation types to score.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @staticmethod
    def _score(text: str, topic: str) -> tuple[str, float, str]:
        t = text.lower()
        pos_markers = ["because", "therefore", "should", "important", "benefit"]
        neg_markers = ["however", "against", "risk", "harm", "problem"]
        pos = sum(1 for m in pos_markers if m in t)
        neg = sum(1 for m in neg_markers if m in t)
        topic_hit = 1 if topic and topic.lower() in t else 0
        if pos > neg:
            label = "Argument_for"
        elif neg > pos:
            label = "Argument_against"
        else:
            label = "NoArgument"
        confidence = min(0.99, 0.5 + 0.1 * abs(pos - neg) + 0.1 * topic_hit)
        reason = f"pos={pos}, neg={neg}, topic_hit={topic_hit}"
        return label, confidence, reason

    @log_errors(recovery_suggestion="Check incoming text spans and argument parameters.")
    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        logger = get_event_logger_or_none()
        topic = str(doc.parameters.get("topic") or "general")
        selection_types_raw = str(doc.parameters.get("selection_types") or "").strip()
        selection_types = {s.strip() for s in selection_types_raw.split(",") if s.strip()}
        text = sofa_text_value(doc.sofa) or ""
        if logger:
            await logger.info(
                "Argument processing started",
                {"characters": len(text), "topic": topic, "incoming_fs": len(doc.fs)},
            )
            await logger.debug("Argument parameters resolved", {"parameters": dict(doc.parameters)})

        spans = [
            fs
            for fs in doc.fs
            if fs.begin is not None and fs.end is not None and fs.end > fs.begin and (not selection_types or fs.type in selection_types)
        ]
        if not spans and text:
            spans = [FeatureStructure(type="uima.tcas.Annotation", begin=0, end=len(text), features={})]

        annotations = 0
        feature_structures = 0
        for span in spans:
            covered = text[span.begin : span.end] if text else ""
            label, confidence, reason = self._score(covered, topic)

            annotations += 1
            feature_structures += 1
            yield Argument(
                        begin=span.begin,
                        end=span.end,
                        topic=topic,
                        reason=reason,
                        features={
                            "label": label,
                            "confidence": round(confidence, 3),
                        },
            )
            yield AnnotationComment(
                        begin=span.begin,
                        end=span.end,
                        key="label",
                        value=label,
            )

        elapsed_ms = int((time() - started) * 1000)
        if logger:
            await logger.metric("processing", "argument_spans_scored", len(spans), "count", elapsed_ms)
            await logger.metric("processing", "argument_annotations", annotations, "count", elapsed_ms)
            await logger.metric("processing", "argument_feature_structures", feature_structures, "count", elapsed_ms)
            await logger.info(
                "Argument processing completed",
                {
                    "spans": len(spans),
                    "annotations": annotations,
                    "feature_structures": feature_structures,
                    "elapsed_ms": elapsed_ms,
                },
            )

        yield AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName="heuristic-argument",
                modelVersion="1",
        )
        yield DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} heuristic argument classification",
        )


app = create_app(ArgumentAnnotator, request_adapter=AsyncChunkedRequestAdapter())
