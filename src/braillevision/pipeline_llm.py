"""Pipeline C: GPT-4o Vision API for Braille recognition."""

import base64
import math
import os
import time
from dataclasses import dataclass

import cv2
import numpy as np
from openai import OpenAI

SYSTEM_PROMPT = """You are a specialized Braille image interpreter.

Your only task is to inspect an image containing Braille cells,
identify the Braille dot patterns, and translate them into English text.

Rules:
1. Treat the image as Braille unless it is clearly not Braille.
2. Identify each Braille cell from left to right.
3. Use standard 6-dot English Braille unless the image clearly uses 8-dot Braille.
4. For each cell, determine which dots are raised using this numbering:

   1 4
   2 5
   3 6

5. Translate the Braille cells into English letters, numbers, or punctuation.
6. Output only the final English translation unless the user explicitly asks for reasoning.
7. If the Braille is ambiguous, say the most likely reading and briefly mention the ambiguity.
8. Do not identify people, objects, or unrelated image details.
9. Do not hallucinate missing cells. If a cell is unreadable, use [?].
10. Preserve spaces if visible gaps between Braille cells indicate word breaks.

Example:
Image shows cells:
dots 1-2-5, dots 1-5, dots 1-2-3, dots 1-2-3, dots 1-3-5
Output:
hello"""

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
