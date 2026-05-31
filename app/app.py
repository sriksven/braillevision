"""Flask web app for BrailleVision."""

from __future__ import annotations

import itertools
import threading
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from PIL import Image, ImageDraw

load_dotenv()

from braillevision.pipeline import PipelineResult, run_pipeline
from braillevision.recognition import CAPITAL_INDICATOR, pattern_for_char
from braillevision.utils import encode_jpeg, image_to_data_url, load_image

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"
SAMPLES.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
state_lock = threading.Lock()
latest_result: PipelineResult | None = None
latest_frame: np.ndarray | None = None
worker_started = False


def _ensure_samples() -> None:
    if any(SAMPLES.glob("*.*")):
        return
    for text in ("hello", "world", "test"):
        Image.fromarray(_generate_demo_braille(text)).save(SAMPLES / f"{text}.png")


def _generate_demo_braille(text: str) -> np.ndarray:
    img = Image.new("RGB", (420, 220), "white")
    draw = ImageDraw.Draw(img)
    x = 36
    for char in text:
        patterns = []
        if char.isupper():
            patterns.append(CAPITAL_INDICATOR)
        patterns.append(pattern_for_char(char))
        for pat in patterns:
            for idx, enabled in enumerate(pat):
                if not enabled:
                    continue
                col = idx // 3
                row = idx % 3
                cx = x + col * 22
                cy = 36 + row * 22
                draw.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(28, 28, 28))
            x += 64
    return np.asarray(img)


def _overlay_demo(frame: np.ndarray) -> np.ndarray:
    img = Image.fromarray(frame.astype(np.uint8)).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rectangle((12, 12, 128, 42), fill=(26, 24, 20))
    draw.text((22, 19), "DEMO MODE", fill=(255, 255, 255))
    return np.asarray(img)


def _result_json(result: PipelineResult | None) -> dict[str, object]:
    if result is None:
        return {
            "text": "",
            "dot_count": 0,
            "cell_count": 0,
            "confidence": 0.0,
            "spacing": 0.0,
        }
    return {
        "text": result.text,
        "dot_count": result.dot_count,
        "cell_count": result.cell_count,
        "confidence": result.confidence,
        "spacing": result.dot_spacing,
    }


def _demo_worker() -> None:
    global latest_frame, latest_result
    _ensure_samples()
    sample_cycle = itertools.cycle(sorted(SAMPLES.glob("*.*")))
    while True:
        path = next(sample_cycle)
        try:
            frame = load_image(path)
            result = run_pipeline(frame)
            annotated = _overlay_demo(result.annotated_frame)
            result.annotated_frame = annotated
            with state_lock:
                latest_result = result
                latest_frame = annotated
        except Exception:
            pass
        time.sleep(4.0)


def _start_worker_once() -> None:
    global worker_started
    if worker_started:
        return
    worker_started = True
    thread = threading.Thread(target=_demo_worker, daemon=True)
    thread.start()


@app.before_request
def start_background_worker() -> None:
    _start_worker_once()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "1.0"})


@app.route("/result")
def result():
    with state_lock:
        return jsonify(_result_json(latest_result))


@app.route("/video_feed")
def video_feed():
    def generate():
        while True:
            with state_lock:
                frame = (
                    latest_frame.copy()
                    if latest_frame is not None
                    else np.full((220, 320, 3), 245, dtype=np.uint8)
                )
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + encode_jpeg(
                frame
            ) + b"\r\n"
            time.sleep(0.1)

    return app.response_class(
        generate(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"error": "missing image file"}), 400
    uploaded = request.files["image"]
    if uploaded.filename == "":
        return jsonify({"error": "empty filename"}), 400

    path = SAMPLES / f"upload_{int(time.time())}_{Path(uploaded.filename).name}"
    uploaded.save(path)
    frame = load_image(path)
    result = run_pipeline(frame)
    with state_lock:
        global latest_result, latest_frame
        latest_result = result
        latest_frame = result.annotated_frame

    payload = _result_json(result)
    payload["annotated_image_b64"] = image_to_data_url(result.annotated_frame)
    return jsonify(payload)


@app.route("/upload_ensemble", methods=["POST"])
def upload_ensemble():
    """Run all four pipelines in ensemble mode."""
    if "image" not in request.files:
        return jsonify({"error": "missing image file"}), 400
    uploaded = request.files["image"]
    if uploaded.filename == "":
        return jsonify({"error": "empty filename"}), 400

    path = SAMPLES / f"upload_{int(time.time())}_{Path(uploaded.filename).name}"
    uploaded.save(path)
    frame = load_image(path)

    from braillevision.pipeline_ensemble import run_ensemble_pipeline

    result = run_ensemble_pipeline(frame)

    return jsonify(
        {
            "final_text": result.final_text,
            "final_confidence": round(result.final_confidence, 3),
            "agreement": result.agreement,
            "winner": result.winner,
            "pipeline_a": {
                "text": result.pipeline_a_text,
                "confidence": round(result.pipeline_a_confidence, 3),
                "latency_ms": result.pipeline_a_latency_ms,
            },
            "pipeline_b": {
                "text": result.pipeline_b_text,
                "confidence": round(result.pipeline_b_confidence, 3),
                "latency_ms": result.pipeline_b_latency_ms,
            },
            "pipeline_c": {
                "text": result.pipeline_c_text,
                "confidence": round(result.pipeline_c_confidence, 3),
                "latency_ms": result.pipeline_c_latency_ms,
            },
            "pipeline_d": {
                "text": result.pipeline_d_text,
                "confidence": round(result.pipeline_d_confidence, 3),
                "latency_ms": result.pipeline_d_latency_ms,
            },
        }
    )


if __name__ == "__main__":
    _start_worker_once()
    app.run(host="0.0.0.0", port=7860, debug=True, threaded=True)
