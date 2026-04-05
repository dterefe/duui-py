from __future__ import annotations

import base64
import tempfile
from functools import lru_cache
from pathlib import Path
from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import AnnotationMeta, DocumentModification, DuuiDocument, DuuiResult
from duui_py.models.uima import Annotation


class AudioToken(Annotation):
    type: str = "org.texttechnologylab.annotation.type.AudioToken"


@lru_cache(maxsize=4)
def _load_whisper_model(model_name: str):
    import whisper  # Optional runtime dependency

    return whisper.load_model(model_name)


class WhisperAnnotator(DuuiAnnotator[DuuiDocument, DuuiResult]):
    config_path = "annotator_config.json"

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    def _extract_audio_bytes(self, doc: DuuiDocument) -> bytes:
        if isinstance(doc.sofa.data, (bytes, bytearray)):
            return bytes(doc.sofa.data)

        b64_candidates: list[str] = []
        if isinstance(doc.sofa.data, str) and doc.sofa.data.strip():
            b64_candidates.append(doc.sofa.data.strip())

        for key in ("audio", "audio_base64"):
            value = doc.parameters.get(key)
            if isinstance(value, str) and value.strip():
                b64_candidates.append(value.strip())

        for candidate in b64_candidates:
            raw = candidate
            if "," in raw and "base64" in raw.split(",", 1)[0]:
                raw = raw.split(",", 1)[1]
            try:
                return base64.b64decode(raw, validate=False)
            except Exception:
                continue

        return b""

    async def process(self, doc: DuuiDocument) -> DuuiResult:
        model_name = str(doc.parameters.get("model_name") or "base")
        file_suffix = str(doc.parameters.get("file_suffix") or ".mp3")

        audio_bytes = self._extract_audio_bytes(doc)
        if not audio_bytes:
            return DuuiResult(errors=["No audio payload found. Provide bytes SofA or base64 audio in sofa/parameters."])

        try:
            model = _load_whisper_model(model_name)
        except Exception as exc:  # noqa: BLE001
            return DuuiResult(errors=[f"Whisper model load failed ({model_name}): {exc}"])

        with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            audio_path = Path(tmp.name)

        tokens: list[AudioToken] = []
        try:
            result = model.transcribe(str(audio_path), word_timestamps=False)
            for segment in result.get("segments", []):
                text = str(segment.get("text", "")).strip()
                tokens.append(
                    AudioToken(
                        begin=0,
                        end=0,
                        features={
                            "timeStart": float(segment.get("start", 0.0)),
                            "timeEnd": float(segment.get("end", 0.0)),
                            "value": text,
                        },
                    )
                )
        finally:
            audio_path.unlink(missing_ok=True)

        return DuuiResult(
            annotations=tokens,
            meta=AnnotationMeta(
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
