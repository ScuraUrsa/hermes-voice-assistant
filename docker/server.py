#!/usr/bin/env python3
"""
Kokoro-F5 TTS Wyoming Protocol Server

Implements the Wyoming TTS protocol over WebSocket.
Accepts synthesis requests at /synthesize and returns WAV audio.

Wyoming protocol:
- Client sends JSON with "text" and optional "voice" fields
- Server responds with WAV binary audio data

Run: uvicorn server:app --host 0.0.0.0 --port 10200
"""

import io
import json
import logging
import os
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wyoming-kokoro")

app = FastAPI(title="Kokoro TTS (Wyoming Protocol)")

# ---------------------------------------------------------------------------
# Kokoro TTS engine — lazy-loaded on first request
# ---------------------------------------------------------------------------
_tts_pipeline = None

def get_tts_pipeline():
    global _tts_pipeline
    if _tts_pipeline is None:
        try:
            from kokoro import KPipeline
            logger.info("Loading Kokoro TTS pipeline...")
            # Use Polish voice by default; override via voice param
            _tts_pipeline = KPipeline(lang_code='a')
            logger.info("Kokoro pipeline loaded.")
        except Exception as exc:
            logger.error("Failed to load Kokoro pipeline: %s", exc)
            raise
    return _tts_pipeline


def synthesize(text: str, voice: str = "af_heart") -> bytes:
    """
    Run Kokoro TTS on *text* and return WAV bytes.
    """
    pipeline = get_tts_pipeline()
    # Generate audio generator
    gen = pipeline(text, voice=voice, speed=1.0)
    audio_chunks = []
    sample_rate = None
    for result in gen:
        if sample_rate is None:
            sample_rate = getattr(result, 'sr', 24000)
        audio_chunks.append(result.audio)

    if not audio_chunks:
        raise RuntimeError("Kokoro produced no audio output")

    full_audio = np.concatenate(audio_chunks) if len(audio_chunks) > 1 else audio_chunks[0]

    # Write WAV to bytes buffer
    buf = io.BytesIO()
    sf.write(buf, full_audio, samplerate=sample_rate or 24000, format='WAV')
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# REST health endpoint (used by Docker HEALTHCHECK)
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "wyoming-kokoro-tts"}


# ---------------------------------------------------------------------------
# Wyoming TTS WebSocket endpoint
# ---------------------------------------------------------------------------
@app.websocket("/synthesize")
async def wyoming_synthesize(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket connection accepted")

    try:
        while True:
            # Receive text message (JSON with "text" and optional "voice")
            data = await ws.receive_text()
            payload = json.loads(data)
            text = payload.get("text", "").strip()
            voice = payload.get("voice", "af_heart")

            if not text:
                await ws.send_text(json.dumps({"error": "Empty text"}))
                continue

            logger.info("Synthesizing text='%s' voice='%s'", text[:80], voice)

            try:
                wav_bytes = synthesize(text, voice=voice)
                # Send binary WAV data
                await ws.send_bytes(wav_bytes)
            except Exception as exc:
                logger.error("Synthesis error: %s", exc)
                await ws.send_text(json.dumps({"error": str(exc)}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as exc:
        logger.warning("Connection error: %s", exc)


# ---------------------------------------------------------------------------
# Simple HTTP fallback: POST /synthesize returning WAV directly
# ---------------------------------------------------------------------------
@app.post("/synthesize")
async def synthesize_http(text: str = "", voice: str = "af_heart"):
    if not text:
        return Response(
            content=json.dumps({"error": "Missing 'text' parameter"}),
            media_type="application/json",
            status_code=400,
        )
    logger.info("HTTP synthesize: text='%s' voice='%s'", text[:80], voice)
    wav_bytes = synthesize(text, voice=voice)
    return Response(content=wav_bytes, media_type="audio/wav")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "10200"))
    uvicorn.run(app, host="0.0.0.0", port=port)