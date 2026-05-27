from __future__ import annotations
from collections.abc import AsyncIterator
from collections import Counter
from time import time
from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.telemetry import telemetry
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
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import EssayScore

DIV_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Div"


class EssayScorerAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"example": "duui-llm-essay-scorer migration"}),
        descriptor=AnnotatorDescriptor(
            name="essay-scorer-msgpack-lua",
            version="1.0.0",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
                annotation=DomainSpec(
                    default=Domain(
                        mimeType="application/x-uima-annotation-spans",
                        languages=["x-unspecified"],
                        types={"Span": [DIV_TYPE]},
                    )
                ),
            ),
            output=IODescriptor(
                types={"EssayScore": ["org.texttechnologylab.annotation.EssayScore"]},
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemEssayScorer.xml",
        parameters_schema={
            "name_model": {
                "type": "string",
                "default": "heuristic-essay-scorer",
                "description": "Model label added to metadata.",
            }
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @staticmethod
    def _heuristic_score(text: str) -> tuple[float, str]:
        words = [w for w in text.split() if w]
        if not words:
            return (0.0, "Empty answer")
        uniq_ratio = len(set((w.lower() for w in words))) / len(words)
        length_factor = min(1.0, len(words) / 180.0)
        punct = Counter((ch for ch in text if ch in ".,;:!?"))
        cohesion = min(1.0, sum(punct.values()) / max(1, len(words)) * 8.0)
        score = round(
            (0.5 * length_factor + 0.3 * uniq_ratio + 0.2 * cohesion) * 6.0, 3
        )
        reason = f"length_factor={length_factor:.3f}, uniq_ratio={uniq_ratio:.3f}, cohesion={cohesion:.3f}"
        return (score, reason)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        model_label = str(doc.parameters.get("name_model") or "heuristic-essay-scorer")
        await telemetry.info(
            "Essay scoring started", model=model_label, text_length=len(text)
        )
        divs = [
            fs
            for fs in doc.fs
            if fs.begin is not None
            and fs.end is not None
            and (fs.type == DIV_TYPE)
            and (fs.end > fs.begin)
        ]
        if not divs and text:
            divs = [
                FeatureStructure(
                    type=DIV_TYPE,
                    begin=0,
                    end=len(text),
                    features={"id": "full-document"},
                )
            ]
        scores = 0
        for div in divs:
            covered = text[div.begin : div.end] if text else ""
            score, reason = self._heuristic_score(covered)
            div_id = str(div.features.get("id") or "full-document")
            scores += 1
            yield EssayScore(
                begin=div.begin,
                end=div.end,
                Value=score,
                Name="EssayScore",
                Reason=reason,
                features={"inputAnswer": div_id, "NameModel": model_label},
            )
        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count("essay_spans_scored", scores, model=model_label)
        await telemetry.timing("essay_processing_ms", elapsed_ms)
        await telemetry.info(
            "Essay scoring completed", scores=scores, elapsed_ms=elapsed_ms
        )
        yield AnnotatorMetaData(
            name=self.config.descriptor.name,
            version=self.config.descriptor.version,
            modelName=model_label,
            modelVersion="1",
        )
        yield DocumentModification(
            user=self.config.descriptor.name,
            timestamp=int(time()),
            comment=f"{self.config.descriptor.name} heuristic essay scoring",
        )


app = create_app(EssayScorerAnnotator, request_adapter=AsyncChunkedRequestAdapter())
