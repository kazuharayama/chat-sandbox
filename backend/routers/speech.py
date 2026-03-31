import asyncio

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel

from core.dependencies import get_speech_service

router = APIRouter()


class TTSRequest(BaseModel):
    text: str


@router.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    try:
        service = get_speech_service()
        audio_bytes = await audio.read()
        text = await asyncio.to_thread(service.transcribe, audio_bytes)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音声認識中にエラーが発生しました: {str(e)}")


@router.post("/text-to-speech")
async def text_to_speech(request: TTSRequest):
    try:
        service = get_speech_service()
        wav_bytes = await asyncio.to_thread(service.synthesize, request.text)
        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": "inline; filename=speech.wav"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音声合成中にエラーが発生しました: {str(e)}")
