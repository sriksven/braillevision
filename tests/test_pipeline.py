from braillevision.pipeline import run_pipeline


def test_blank_pipeline_returns_empty(blank_frame):
    result = run_pipeline(blank_frame)
    assert result.text == ""
    assert result.dot_count == 0
    assert result.annotated_frame.shape[:2] == blank_frame.shape[:2]


def test_synthetic_hello_pipeline(synthetic_hello):
    result = run_pipeline(synthetic_hello)
    assert result.text == "hello"
    assert result.confidence >= 0.8
    assert result.cell_count == 5


def test_pipeline_parametrized_words(synthetic_text):
    for text in ["abc", "hello", "world", "test"]:
        result = run_pipeline(synthetic_text(text))
        assert result.text == text
        assert result.confidence >= 0.8
