"""Tests for LLM pipeline."""

from unittest.mock import MagicMock, patch

import numpy as np

from braillevision.pipeline_llm import run_llm_pipeline


def test_llm_no_key_returns_error():
    """Test that missing API key returns error."""
    frame = np.ones((100, 100, 3), dtype=np.uint8)
    with patch.dict("os.environ", {}, clear=False):
        with patch("braillevision.pipeline_llm.os.getenv", return_value=""):
            result = run_llm_pipeline(frame, api_key="")
    assert result.error is not None
    assert result.text == ""
    assert result.confidence == 0.0


def test_llm_api_failure():
    """Test that API failure is handled gracefully."""
    frame = np.ones((100, 100, 3), dtype=np.uint8)
    with patch("braillevision.pipeline_llm.OpenAI") as mock_client_class:
        mock_client_class.return_value.chat.completions.create.side_effect = Exception(
            "API error"
        )
        result = run_llm_pipeline(frame, api_key="test-key")
    assert result.error is not None
    assert result.text == ""
    assert result.confidence == 0.0


def test_llm_unclear_response():
    """Test that UNCLEAR response returns empty text."""
    frame = np.ones((100, 100, 3), dtype=np.uint8)
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "UNCLEAR"
    with patch("braillevision.pipeline_llm.OpenAI") as mock_client_class:
        mock_client_class.return_value.chat.completions.create.return_value = mock_resp
        result = run_llm_pipeline(frame, api_key="test-key")
    assert result.text == ""
    assert result.confidence == 0.1


def test_llm_valid_response():
    """Test that valid response is processed correctly."""
    frame = np.ones((100, 100, 3), dtype=np.uint8)
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "hello world"
    with patch("braillevision.pipeline_llm.OpenAI") as mock_client_class:
        mock_client_class.return_value.chat.completions.create.return_value = mock_resp
        result = run_llm_pipeline(frame, api_key="test-key")
    assert result.text == "hello world"
    assert result.confidence == 0.92
    assert result.latency_ms >= 0  # May be 0 due to mock speed
    assert result.model == "gpt-4o"
