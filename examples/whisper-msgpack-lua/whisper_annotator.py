from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path
from time import time

from collections.abc import AsyncIterable

from duui_py.annotator import DuuiAnnotator, V1AsyncProcess, V1Payload
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
    DuuiError,
    IODescriptor,
)
from duui_py.models.uima import SoFaBytes
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import AudioToken


@lru_cache(maxsize=4)
def _load_whisper_model(model_name: str):
    import whisper  # Optional runtime dependency

    return whisper.load_model(model_name)


class WhisperAnnotator(DuuiAnnotator[object, object], V1AsyncProcess[V1Payload]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(),
        descriptor=AnnotatorDescriptor(
            name="whisper-msgpack-lua",
            version="1.0.0",
            input=IODescriptor(
                bytes=DomainSpec(
                    default=Domain(
                        mimeType="application/octet-stream",
                        languages=["x-unspecified"],
                    )
                )
            ),
            output=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                        types={"AudioToken": ["org.texttechnologylab.annotation.type.AudioToken"]},
                    )
                )
            ),
        ),
        typesystem_xml_path="TypeSystemWhisper.xml",
        parameters_schema={
            "model_name": {
                "type": "string",
                "default": "base",
                "description": "OpenAI Whisper model name.",
            },
            "use_dummy": {
                "type": "boolean",
                "default": False,
                "description": "Skip Whisper model load/transcribe and emit deterministic dummy token.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @log_errors(recovery_suggestion="Whisper pass-through process received an invalid DUUI result.")
    async def process(self, doc: object) -> object:
        return doc

    async def process_bytes(
        self, sofa: SoFaBytes, payload: V1Payload, parameters: dict[str, object]
    ) -> AsyncIterable[object]:
        del payload
        started = time()
        logger = get_event_logger_or_none()
        model_name = str(parameters.get("model_name") or "base")
        use_dummy = str(parameters.get("use_dummy") or "").lower() in {"1", "true", "yes", "on"}
        audio_bytes = bytes(sofa.bytes)
        if logger:
            await logger.info(
                "Whisper processing started",
                {"bytes": len(audio_bytes), "model": model_name, "use_dummy": use_dummy},
            )
            await logger.debug("Whisper parameters resolved", {"parameters": dict(parameters)})

        if not audio_bytes:
            if logger:
                await logger.error_event(
                    error_type="EmptyAudioPayload",
                    message="No audio payload found in Sofa bytes.",
                    recovery_suggestion="Send a non-empty byte sofa.",
                    extra={"model": model_name},
                )
            yield DuuiError(message="No audio payload found in Sofa bytes.")
            return

        if use_dummy:
            elapsed_ms = int((time() - started) * 1000)
            if logger:
                await logger.metric("processing", "whisper_audio_tokens", 1, "count", elapsed_ms)
                await logger.info(
                    "Whisper processing completed",
                    {"mode": "dummy", "tokens": 1, "elapsed_ms": elapsed_ms},
                )
            yield AudioToken(begin=0, end=0, timeStart=0.0, timeEnd=0.0, value=f"dummy-bytes-{len(audio_bytes)}")
            yield AnnotatorMetaData(
                    name=self.config.descriptor.name,
                    version=self.config.descriptor.version,
                    modelName="dummy",
                    modelVersion="runtime",
            )
            yield DocumentModification(
                    user=self.config.descriptor.name,
                    timestamp=int(time()),
                    comment=f"{self.config.descriptor.name} ({self.config.descriptor.version}) dummy mode",
            )
            return

        try:
            model = _load_whisper_model(model_name)
        except Exception as exc:  # noqa: BLE001
            if logger:
                await logger.error_event(
                    error_type=type(exc).__name__,
                    message=f"Whisper model load failed ({model_name}): {exc}",
                    recovery_suggestion="Install whisper and ensure the requested model is available.",
                    extra={"model": model_name},
                )
            yield DuuiError(message=f"Whisper model load failed ({model_name}): {exc}")
            return

        token_count = 0
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
                token_count += 1
                yield AudioToken(
                    begin=0,
                    end=0,
                    timeStart=float(segment.get("start", 0.0)),
                    timeEnd=float(segment.get("end", 0.0)),
                    value=text,
                )
        except Exception as exc:  # noqa: BLE001
            if logger:
                await logger.error_event(
                    error_type=type(exc).__name__,
                    message=f"Whisper transcribe failed: {exc}",
                    recovery_suggestion="Check that the byte payload is valid audio for Whisper.",
                    extra={"model": model_name},
                )
            yield DuuiError(message=f"Whisper transcribe failed: {exc}")
            return

        elapsed_ms = int((time() - started) * 1000)
        if logger:
            await logger.metric("processing", "whisper_audio_tokens", token_count, "count", elapsed_ms)
            await logger.info(
                "Whisper processing completed",
                {"mode": "whisper", "tokens": token_count, "elapsed_ms": elapsed_ms},
            )

        yield AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName=model_name,
                modelVersion="runtime",
        )
        yield DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} ({self.config.descriptor.version})",
        )


app = create_app(WhisperAnnotator, request_adapter=AsyncChunkedRequestAdapter())
