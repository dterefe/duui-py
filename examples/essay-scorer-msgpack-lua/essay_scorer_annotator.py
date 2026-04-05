from __future__ import annotations

from collections import Counter
from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import AnnotationMeta, DocumentModification, DuuiDocument, DuuiResult
from duui_py.models.uima import Annotation

DIV_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Div"
ESSAY_SCORE_TYPE = "org.texttechnologylab.annotation.EssayScore"


class EssayScore(Annotation):
    type: str = ESSAY_SCORE_TYPE


class EssayScorerAnnotator(DuuiAnnotator[DuuiDocument, DuuiResult]):
    config_path = "annotator_config.json"

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @staticmethod
    def _heuristic_score(text: str) -> tuple[float, str]:
        words = [w for w in text.split() if w]
        if not words:
            return 0.0, "Empty answer"
        uniq_ratio = len(set(w.lower() for w in words)) / len(words)
        length_factor = min(1.0, len(words) / 180.0)
        punct = Counter(ch for ch in text if ch in ".,;:!?")
        cohesion = min(1.0, (sum(punct.values()) / max(1, len(words))) * 8.0)
        score = round((0.5 * length_factor + 0.3 * uniq_ratio + 0.2 * cohesion) * 6.0, 3)
        reason = f"length_factor={length_factor:.3f}, uniq_ratio={uniq_ratio:.3f}, cohesion={cohesion:.3f}"
        return score, reason

    async def process(self, doc: DuuiDocument) -> DuuiResult:
        text = doc.text or ""
        model_label = str(doc.parameters.get("name_model") or "heuristic-essay-scorer")

        divs = [
            fs
            for fs in doc.fs
            if fs.begin is not None and fs.end is not None and fs.type == DIV_TYPE and fs.end > fs.begin
        ]

        if not divs and text:
            from duui_py.models import FsRec

            divs = [FsRec(id=1, type=DIV_TYPE, begin=0, end=len(text), features={"id": "full-document"})]

        annotations: list[EssayScore] = []
        for div in divs:
            covered = text[div.begin : div.end] if text else ""
            score, reason = self._heuristic_score(covered)
            div_id = str(div.features.get("id") or div.id)
            annotations.append(
                EssayScore(
                    begin=div.begin,
                    end=div.end,
                    features={
                        "value": score,
                        "name": "EssayScore",
                        "reason": reason,
                        "inputAnswer": div_id,
                        "NameModel": model_label,
                    },
                )
            )

        return DuuiResult(
            annotations=annotations,
            meta=AnnotationMeta(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName=model_label,
                modelVersion="1",
            ),
            modification_meta=DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} heuristic essay scoring",
            ),
        )


app = create_app(EssayScorerAnnotator)
