"""Orchestrator: run all four pipelines in parallel threads."""

import os
import threading

import numpy as np
from dotenv import load_dotenv

from .ensemble import EnsembleResult, ensemble
from .pipeline import run_pipeline
from .pipeline_finetuned import run_finetuned_pipeline
from .pipeline_llm import run_llm_pipeline
from .pipeline_roboflow import run_roboflow_pipeline

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def run_ensemble_pipeline(
    frame: np.ndarray,
    on_ab_ready=None,
    on_complete=None,
) -> EnsembleResult:
    """
    Run all four pipelines in parallel threads.

    A, B, D are local - finish in ~300ms.
    C is an API call - finishes in ~2-4s.

    on_ab_ready fires when A, B, D are all done (instant results for UI).
    on_complete fires when all four are done.
    """
    results = {"a": None, "b": None, "c": None, "d": None}
    lock = threading.Lock()

    def run_a():
        r = run_pipeline(frame)
        with lock:
            results["a"] = r

    def run_b():
        r = run_roboflow_pipeline(frame)
        with lock:
            results["b"] = r

    def run_c():
        r = run_llm_pipeline(frame, api_key=OPENAI_API_KEY)
        with lock:
            results["c"] = r

    def run_d():
        r = run_finetuned_pipeline(frame)
        with lock:
            results["d"] = r

    threads = {
        "a": threading.Thread(target=run_a, daemon=True),
        "b": threading.Thread(target=run_b, daemon=True),
        "c": threading.Thread(target=run_c, daemon=True),
        "d": threading.Thread(target=run_d, daemon=True),
    }

    for t in threads.values():
        t.start()

    # Wait for local pipelines first (fast)
    for key in ("a", "b", "d"):
        threads[key].join()

    if on_ab_ready:
        on_ab_ready(results["a"], results["b"], results["d"])

    # Wait for API call
    threads["c"].join()

    a, b, c, d = results["a"], results["b"], results["c"], results["d"]

    result = ensemble(
        a_text=a.text if a else "",
        a_conf=a.confidence if a else 0.0,
        a_lat=getattr(a, "latency_ms", 0) if a else 0,
        b_text=b.text if b else "",
        b_conf=b.confidence if b else 0.0,
        b_lat=b.latency_ms if b else 0,
        c_text=c.text if c else "",
        c_conf=c.confidence if c else 0.0,
        c_lat=c.latency_ms if c else 0,
        d_text=d.text if d else "",
        d_conf=d.confidence if d else 0.0,
        d_lat=d.latency_ms if d else 0,
    )

    if on_complete:
        on_complete(result)

    return result
