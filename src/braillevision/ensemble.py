"""Ensemble layer: weighted voting across four pipelines."""

from dataclasses import dataclass

try:
    import Levenshtein

    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False


@dataclass
class EnsembleResult:
    final_text: str
    final_confidence: float
    pipeline_a_text: str
    pipeline_a_confidence: float
    pipeline_a_latency_ms: int
    pipeline_b_text: str
    pipeline_b_confidence: float
    pipeline_b_latency_ms: int
    pipeline_c_text: str
    pipeline_c_confidence: float
    pipeline_c_latency_ms: int
    agreement: str  # "full" | "majority" | "none"
    winner: str  # "A" | "B" | "C" | "none"


def _similarity(a: str, b: str) -> float:
    """Calculate text similarity using Levenshtein distance."""
    if not LEVENSHTEIN_AVAILABLE:
        return 1.0 if a.lower().strip() == b.lower().strip() else 0.0

    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    dist = Levenshtein.distance(a.lower().strip(), b.lower().strip())
    return 1.0 - dist / max(len(a), len(b), 1)


def ensemble(
    a_text: str,
    a_conf: float,
    a_lat: int,
    b_text: str,
    b_conf: float,
    b_lat: int,
    c_text: str,
    c_conf: float,
    c_lat: int,
) -> EnsembleResult:
    """
    Weighted voting across three pipelines.

    Weights reflect expected accuracy (normalized to not overpower pure 100% confidence):
      A (classical CV)     = 1.00
      B (Roboflow model)   = 1.02
      C (GPT-4o Vision)    = 1.05

    Agreement bonus: pairwise agreement boosts combined weight by 1.3x.
    """
    texts = [a_text, b_text, c_text]
    confs = [a_conf, b_conf, c_conf]
    weights = [1.00, 1.02, 1.05]
    labels = ["A", "B", "C"]
    THRESHOLD = 0.85

    # All pairwise similarities
    pairs = [(0, 1), (0, 2), (1, 2)]
    agreements = {
        (i, j): _similarity(texts[i], texts[j]) >= THRESHOLD for i, j in pairs
    }

    # Agreement bonus per pipeline
    for (i, j), agrees in agreements.items():
        if agrees:
            weights[i] *= 1.3
            weights[j] *= 1.3

    # Count agreeing pipelines
    agreeing = sum(1 for (i, j), a in agreements.items() if a)
    if agreeing == 3:
        agreement = "full"
    elif agreeing >= 1:
        agreement = "majority"
    else:
        agreement = "none"

    # Final weighted scores
    scores = [w * c for w, c in zip(weights, confs)]

    best_idx = -1
    best_score = -1.0
    for i, (text, score) in enumerate(zip(texts, scores)):
        if text and score > best_score:
            best_score = score
            best_idx = i

    if best_idx == -1:
        return EnsembleResult(
            final_text="",
            final_confidence=0.0,
            pipeline_a_text=a_text,
            pipeline_a_confidence=a_conf,
            pipeline_a_latency_ms=a_lat,
            pipeline_b_text=b_text,
            pipeline_b_confidence=b_conf,
            pipeline_b_latency_ms=b_lat,
            pipeline_c_text=c_text,
            pipeline_c_confidence=c_conf,
            pipeline_c_latency_ms=c_lat,
            agreement=agreement,
            winner="none",
        )

    final_conf = min(
        0.99,
        confs[best_idx] * (1.1 if agreement != "none" else 1.0),
    )

    return EnsembleResult(
        final_text=texts[best_idx],
        final_confidence=final_conf,
        pipeline_a_text=a_text,
        pipeline_a_confidence=a_conf,
        pipeline_a_latency_ms=a_lat,
        pipeline_b_text=b_text,
        pipeline_b_confidence=b_conf,
        pipeline_b_latency_ms=b_lat,
        pipeline_c_text=c_text,
        pipeline_c_confidence=c_conf,
        pipeline_c_latency_ms=c_lat,
        agreement=agreement,
        winner=labels[best_idx],
    )
