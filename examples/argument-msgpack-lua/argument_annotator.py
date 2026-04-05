from __future__ import annotations

from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import (
    AnnotationMeta,
    DocumentModification,
    DuuiDocument,
    DuuiResult,
    FeatureStructureKeyRef,
    FeatureStructureNode,
)

ARGUMENT_TYPE = "org.texttechnologylab.annotation.Argument"
COMMENT_TYPE = "org.texttechnologylab.annotation.AnnotationComment"


class ArgumentAnnotator(DuuiAnnotator[DuuiDocument, DuuiResult]):
    config_path = "annotator_config.json"

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

    async def process(self, doc: DuuiDocument) -> DuuiResult:
        topic = str(doc.parameters.get("topic") or "general")
        selection_types_raw = str(doc.parameters.get("selection_types") or "").strip()
        selection_types = {s.strip() for s in selection_types_raw.split(",") if s.strip()}

        spans = [
            fs
            for fs in doc.fs
            if fs.begin is not None and fs.end is not None and fs.end > fs.begin and (not selection_types or fs.type in selection_types)
        ]
        if not spans and doc.text:
            from duui_py.models import FsRec

            spans = [FsRec(id=1, type="uima.tcas.Annotation", begin=0, end=len(doc.text), features={})]

        text = doc.text or ""
        nodes: list[FeatureStructureNode] = []

        for i, span in enumerate(spans):
            covered = text[span.begin : span.end] if text else ""
            label, confidence, reason = self._score(covered, topic)

            arg_key = f"arg-{i}"
            nodes.append(
                FeatureStructureNode(
                    key=arg_key,
                    type=ARGUMENT_TYPE,
                    begin=span.begin,
                    end=span.end,
                    features={"topic": topic},
                )
            )

            comment_specs = [
                ("label", label),
                ("confidence", f"{confidence:.3f}"),
                ("reason", reason),
            ]
            comment_refs: list[FeatureStructureKeyRef] = []
            for j, (key, value) in enumerate(comment_specs):
                comment_key = f"arg-{i}-comment-{j}"
                comment_refs.append(FeatureStructureKeyRef(key=comment_key))
                nodes.append(
                    FeatureStructureNode(
                        key=comment_key,
                        type=COMMENT_TYPE,
                        features={
                            "reference": FeatureStructureKeyRef(key=arg_key),
                            "key": key,
                            "value": value,
                        },
                    )
                )

            nodes[-(len(comment_specs) + 1)].features["arguments"] = comment_refs

        return DuuiResult(
            feature_structures=nodes,
            meta=AnnotationMeta(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName="heuristic-argument",
                modelVersion="1",
            ),
            modification_meta=DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} heuristic argument classification",
            ),
        )


app = create_app(ArgumentAnnotator)
