# Architecture

BrailleVision separates the computer-vision pipeline from the web app. The package under `src/braillevision/` accepts NumPy arrays and returns structured results. The Flask app under `app/` handles HTTP, uploads, streaming, and browser UI state.

## Layers

```text
Browser UI
  -> Flask routes in app/app.py
  -> run_pipeline(frame)
  -> src/braillevision modules
  -> PipelineResult
```

## Core Pipeline

`src/braillevision/pipeline.py` is the public orchestration layer.

```text
frame
  -> preprocessing
  -> detection
  -> noise filtering
  -> segmentation
  -> recognition
  -> annotation
```

### `config.py`

Holds `PipelineConfig`, the single place for tunable constants such as CLAHE strength, blob area bounds, circularity, spacing limits, and frame resize width.

### `preprocessing.py`

Responsibilities:

- Convert BGR/RGB/grayscale inputs to grayscale.
- Apply CLAHE when OpenCV is installed.
- Attempt page-like perspective correction.
- Fall back to the original frame when perspective correction cannot find a reliable quadrilateral.

### `detection.py`

Responsibilities:

- Detect candidate Braille dots.
- Use OpenCV `SimpleBlobDetector` when available.
- Try inverted input so both dark-on-light and light-on-dark images can work.
- Provide a connected-component fallback for environments without OpenCV.
- Remove far outliers before segmentation.

### `segmentation.py`

Responsibilities:

- Estimate within-cell dot spacing.
- Group x positions into cell columns.
- Group y positions into text rows.
- Convert dot coordinates inside each cell to Braille positions 1 through 6.

The implementation is deterministic and geometry-based. Real images may still require tuning in `PipelineConfig`.

### `recognition.py`

Responsibilities:

- Decode six-bit Braille patterns to text.
- Support Grade 1 letters and punctuation.
- Handle capital and number indicators.
- Provide a partial table of common Grade 2 contractions.

### `utils.py`

Responsibilities:

- Load images.
- Resize frames.
- Encode JPEG output.
- Draw cell annotations.

### `tts.py`

Contains optional server-side TTS helpers. The current browser UI uses the Web Speech API for speech, so server-side TTS is not part of the main request path.

## Web App

`app/app.py` exposes:

- `GET /`
- `GET /video_feed`
- `GET /result`
- `POST /upload`
- `GET /health`

The app starts a background demo worker that cycles through `data/samples/`, calls `run_pipeline(frame)`, and stores the latest result behind a lock. The browser polls `/result` and renders the MJPEG stream from `/video_feed`.

## Data Flow

```text
data/samples/*.png
  -> demo worker
  -> run_pipeline()
  -> latest_result/latest_frame
  -> /result and /video_feed
```

For uploads:

```text
browser file input
  -> POST /upload
  -> save to data/samples/
  -> run_pipeline()
  -> JSON result plus annotated image data URL
```

## Error Handling

`run_pipeline` catches unexpected processing errors and returns an empty `PipelineResult`. This keeps the live demo from crashing on a single bad frame. During development, use targeted tests or temporary logging to debug failures.

## Current Validation

The latest local validation was run inside `.venv` with OpenCV installed:

```text
OpenCV: 4.13.0
Tests: 20 passed
Coverage: 72%
```

## Real-Image Work

The pipeline is currently tuned for synthetic dot imagery. The next engineering phase is real embossed Braille:

- Collect real images.
- Tune `PipelineConfig`.
- Add annotation JSON.
- Benchmark by condition.
- Report accuracy with real numbers.

