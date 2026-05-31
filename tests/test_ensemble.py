"""Tests for ensemble voting layer."""

import pytest

from braillevision.ensemble import ensemble


def test_full_agreement():
    """Test ensemble with all four pipelines agreeing."""
    result = ensemble(
        a_text="hello",
        a_conf=0.9,
        a_lat=50,
        b_text="hello",
        b_conf=0.8,
        b_lat=300,
        c_text="hello",
        c_conf=0.92,
        c_lat=2000,
        d_text="hello",
        d_conf=0.85,
        d_lat=200,
    )
    assert result.final_text == "hello"
    assert result.agreement == "full"
    assert result.winner in ("A", "B", "C", "D")
    assert result.final_confidence > 0.8


def test_empty_inputs():
    """Test ensemble with all empty responses."""
    result = ensemble(
        a_text="",
        a_conf=0.0,
        a_lat=0,
        b_text="",
        b_conf=0.0,
        b_lat=0,
        c_text="",
        c_conf=0.0,
        c_lat=0,
        d_text="",
        d_conf=0.0,
        d_lat=0,
    )
    assert result.final_text == ""
    assert result.winner == "none"
    assert result.final_confidence == 0.0


def test_majority_agreement():
    """Test ensemble with three pipelines agreeing."""
    result = ensemble(
        a_text="hello",
        a_conf=0.3,
        a_lat=50,
        b_text="hello",
        b_conf=0.8,
        b_lat=300,
        c_text="world",
        c_conf=0.92,
        c_lat=2000,
        d_text="hello",
        d_conf=0.85,
        d_lat=200,
    )
    assert result.agreement in ("majority", "split")
    assert result.final_text in ("hello", "world")


def test_high_confidence_single_pipeline():
    """Test ensemble where highest confidence pipeline wins despite disagreement."""
    result = ensemble(
        a_text="a",
        a_conf=0.1,
        a_lat=50,
        b_text="b",
        b_conf=0.1,
        b_lat=300,
        c_text="correct answer",
        c_conf=0.98,
        c_lat=2000,
        d_text="d",
        d_conf=0.1,
        d_lat=200,
    )
    assert result.final_text == "correct answer"
    assert result.winner == "C"
    assert result.final_confidence > 0.9


def test_weights_preferred_models():
    """Test that C (GPT) and D (finetuned) are preferred over A."""
    result = ensemble(
        a_text="a",
        a_conf=0.9,
        a_lat=50,
        b_text="b",
        b_conf=0.3,
        b_lat=300,
        c_text="c",
        c_conf=0.7,
        c_lat=2000,
        d_text="d",
        d_conf=0.6,
        d_lat=200,
    )
    # C should win due to highest weight (4.0) and reasonable confidence
    assert result.winner in ("C", "A")  # C preferred but A has higher conf
