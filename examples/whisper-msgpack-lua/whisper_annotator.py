from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path
from time import time

from collections.abc import AsyncIterable

from duui_py.annotator import DuuiAnnotator, V1AsyncProcess, V1Payload
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import AnnotatorMetaData, DocumentModification, DuuiResult
from duui_py.models.uima import Annotation, SoFaBytes
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import AudioToken


@lru_cache(maxsize=4)
def _load_whisper_model(model_name: str):
    import whisper  # Optional runtime dependency

    return whisper.load_model(model_name)


class WhisperAnnotator(DuuiAnnotator[DuuiResult, DuuiResult], V1AsyncProcess[V1Payload]):
    config_path = "annotator_config.json"

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: DuuiResult) -> DuuiResult:
        return doc

    async def process_bytes(
        self, sofa: SoFaBytes, payload: V1Payload, parameters: dict[str, object]
    ) -> AsyncIterable[DuuiResult]:
        del payload
        model_name = str(parameters.get("model_name") or "base")
        use_dummy = str(parameters.get("use_dummy") or "").lower() in {"1", "true", "yes", "on"}
        audio_bytes = bytes(sofa.bytes)
        if not audio_bytes:
            yield DuuiResult(errors=["No audio payload found in Sofa bytes."])
            return

        if use_dummy:
            generated = AudioToken(timeStart=0.0, timeEnd=0.0, value=f"dummy-bytes-{len(audio_bytes)}")
            data = generated.model_dump()
            data["begin"] = 0
            data["end"] = 0
            yield DuuiResult(
                annotations=[
                    Annotation.model_validate(data)
                ],
                meta=AnnotatorMetaData(
                    name=self.config.descriptor.name,
                    version=self.config.descriptor.version,
                    modelName="dummy",
                    modelVersion="runtime",
                ),
                modification_meta=DocumentModification(
                    user=self.config.descriptor.name,
                    timestamp=int(time()),
                    comment=f"{self.config.descriptor.name} ({self.config.descriptor.version}) dummy mode",
                ),
            )
            return

        try:
            model = _load_whisper_model(model_name)
        except Exception as exc:  # noqa: BLE001
            yield DuuiResult(errors=[f"Whisper model load failed ({model_name}): {exc}"])
            return

        tokens: list[Annotation] = []
        try:
            with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
                tmp.write(audio_bytes)
                audio_path = Path(tmp.name)
            try:
                result = model.transcribe(str(audio_path))
            finally:
                audio_path.unlink(missing_ok=True)

            for segment in result.get("segments", []):
                text = str(segment.get("text", "")).strip()
                generated = AudioToken(
                    timeStart=float(segment.get("start", 0.0)),
                    timeEnd=float(segment.get("end", 0.0)),
                    value=text,
                )
                data = generated.model_dump()
                data["begin"] = 0
                data["end"] = 0
                tokens.append(Annotation.model_validate(data))
        except Exception as exc:  # noqa: BLE001
            yield DuuiResult(errors=[f"Whisper transcribe failed: {exc}"])
            return

        yield DuuiResult(
            annotations=tokens,
            meta=AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName=model_name,
                modelVersion="runtime",
            ),
            modification_meta=DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} ({self.config.descriptor.version})",
            ),
        )


app = create_app(WhisperAnnotator)
