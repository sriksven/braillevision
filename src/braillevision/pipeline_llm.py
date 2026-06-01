"""Pipeline C: GPT-4o Vision API for Braille recognition."""

import base64
import os
import time
from dataclasses import dataclass

import cv2
import numpy as np
from openai import OpenAI

SYSTEM_PROMPT = (
    "You are an expert at reading Standard English Braille. "
    "The user will provide an image showing Braille dots. "
    "Your ONLY task is to read the Braille characters and output the exact "
    "English text they represent. "
    "Do not guess random words or describe the image. "
    "If the dots are clearly 'h-e-l-l-o', output 'hello'. "
    "Output ONLY the final English text. "
    "Do not add any punctuation, explanations, or formatting. "
    "If the image contains no readable Braille, respond with exactly 'UNCLEAR'."
)

USER_PROMPT = "Read the Braille dots in this image and output only the English text."


@dataclass
class LLMResult:
    text: str
    confidence: float
    latency_ms: int
    model: str = "gpt-4o"
    error: str | None = None


def frame_to_base64(frame: np.ndarray) -> str:
    """Convert frame to JPEG base64 for API."""
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buffer).decode("utf-8")


def run_llm_pipeline(frame: np.ndarray, api_key: str | None = None) -> LLMResult:
    """
    Send frame to GPT-4o Vision API.
    Returns recognized text with confidence and latency.
    """
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        return LLMResult(
            text="",
            confidence=0.0,
            latency_ms=0,
            model="gpt-4o",
            error="No API key provided",
        )

    client = OpenAI(api_key=key)
    b64 = frame_to_base64(frame)
    start = time.time()

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=200,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}",
                                "detail": "high",
                            },
                        },
                        {"type": "text", "text": USER_PROMPT},
                    ],
                },
            ],
        )
        latency_ms = int((time.time() - start) * 1000)
        raw = response.choices[0].message.content.strip()

        if raw in ("UNCLEAR", "NO_BRAILLE"):
            return LLMResult(
                text="", confidence=0.1, latency_ms=latency_ms, model="gpt-4o"
            )

        confidence = 0.92 if len(raw) > 2 else 0.5
        return LLMResult(
            text=raw.lower(),
            confidence=confidence,
            latency_ms=latency_ms,
            model="gpt-4o",
        )

    except Exception as exc:
        return LLMResult(
            text="",
            confidence=0.0,
            latency_ms=int((time.time() - start) * 1000),
            model="gpt-4o",
            error=str(exc),
        )
