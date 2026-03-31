import io
import logging
import subprocess
import tempfile

from core.config import Settings

logger = logging.getLogger(__name__)


class SpeechService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._whisper_model = None

    def _get_whisper_model(self):
        if self._whisper_model is None:
            from faster_whisper import WhisperModel

            self._whisper_model = WhisperModel(
                self._settings.whisper_model_size,
                device=self._settings.whisper_device,
                compute_type=self._settings.whisper_compute_type,
            )
            logger.info("Whisper model loaded: %s", self._settings.whisper_model_size)
        return self._whisper_model

    def transcribe(self, audio_bytes: bytes) -> str:
        """音声バイト列をテキストに変換する (STT)"""
        model = self._get_whisper_model()

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            segments, _ = model.transcribe(
                tmp.name,
                language=self._settings.whisper_language,
                vad_filter=True,
            )
            text = "".join(segment.text for segment in segments)

        logger.info("STT transcribed %d bytes -> %d chars", len(audio_bytes), len(text))
        return text.strip()

    def synthesize(self, text: str) -> bytes:
        """テキストをWAV音声バイト列に変換する (TTS)"""
        result = subprocess.run(
            [
                "piper",
                "--model", self._settings.piper_model_path,
                "--config", self._settings.piper_config_path,
                "--output-raw",
            ],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Piper TTS failed: {result.stderr.decode()}")

        raw_audio = result.stdout
        wav_bytes = self._raw_to_wav(raw_audio)
        logger.info("TTS synthesized %d chars -> %d bytes WAV", len(text), len(wav_bytes))
        return wav_bytes

    @staticmethod
    def _raw_to_wav(raw_audio: bytes, sample_rate: int = 22050, channels: int = 1, sample_width: int = 2) -> bytes:
        """RAW PCMデータをWAVフォーマットに変換する"""
        import wave

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(raw_audio)
        return buf.getvalue()
