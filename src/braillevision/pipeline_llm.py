"""Pipeline C: GPT-4o Vision API for Braille recognition."""

import base64
import math
import os
import time
from dataclasses import dataclass

import cv2
import numpy as np
from openai import OpenAI

SYSTEM_PROMPT = """You are a Braille reading expert.
This image contains physical raised-dot Braille.
Read the Braille dots and output ONLY the English text they spell.
Do not describe the image. Do not say what you see.
Output only the decoded English word or words, nothing else.
If you cannot read it output: UNCLEAR"""

USER_PROMPT = (
    "Translate the Braille in this image into English. Return only the English text."
)


@dataclass
class LLMResult:
    text: str
    confidence: float
    latency_ms: int
    model: str = "gpt-4o"
    error: str | None = None


def frame_to_base64(frame: np.ndarray) -> str:
    """Convert frame to JPEG base64 for API."""
    h, w = frame.shape[:2]
    if min(h, w) < 512:
        scale = 512 / min(h, w)
        frame = cv2.resize(
            frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC
        )
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
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
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            max_tokens=100,
            logprobs=True,
            top_logprobs=1,
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
        choice = response.choices[0]
        raw = choice.message.content.strip()

        if raw in ("UNCLEAR", "NO_BRAILLE"):
            return LLMResult(
                text="", confidence=0.1, latency_ms=latency_ms, model="gpt-4o"
            )

        confidence = 0.5
        if hasattr(choice, "logprobs") and choice.logprobs and choice.logprobs.content:
            probs = [math.exp(token.logprob) for token in choice.logprobs.content]
            if probs:
                confidence = sum(probs) / len(probs)
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
