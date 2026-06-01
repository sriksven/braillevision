---
title: BrailleVision
emoji: 👁
colorFrom: gray
colorTo: green
sdk: docker
app_port: 7860
---

## BrailleVision v2: Three Pipeline Ensemble

**Live demo:** [https://sriksven-braillevision.hf.space](https://sriksven-braillevision.hf.space)

BrailleVision reads camera or uploaded images of Braille and returns English text with speech synthesis. **Version 2 runs three independent recognition pipelines in parallel and combines results using weighted confidence voting.**

### Screenshots

| Upload Interface | Ensemble Results |
|:---:|:---:|
| ![Upload](docs/screenshot_upload.png) | ![Results](docs/screenshot_results.png) |

### Three Pipelines

| Pipeline | Method | Training Data | Latency | Expected Accuracy |
|----------|--------|---------------|---------|-------------------|
| **A** | Classical CV (DBSCAN + lookup) | Rules-based | ~50ms | ~30-50% |
| **B** | Roboflow pretrained YOLOv8 | 1,324 Braille images | ~300ms | ~70-80% |
| **C** | GPT-4o Vision API | Billions of images | ~2-4s | ~90-94% |

**Execution:** A and B return instantly (local inference). C updates when the API responds (~2-4s). Ensemble layer applies **agreement bonuses** - when multiple pipelines agree (Levenshtein similarity >= 0.85), their combined weight increases by 1.3x. Final output goes to TTS.

**Weighted Voting Scheme:**
- Pipeline A (classical CV): weight = 1.0
- Pipeline B (Roboflow YOLOv8): weight = 2.5
- Pipeline C (GPT-4o): weight = 4.0 (highest accuracy potential)

### Key Features

- CLAHE contrast normalization for uneven lighting
- Blob detection for dark-on-light and light-on-dark images
- DBSCAN-based segmentation handling tilted Braille
- Grade 1 Braille lookup with capital and number indicators
- Partial Grade 2 contraction table
- **Three independent recognition pipelines with ensemble voting**
- **Progressive UI showing partial results from A and B while C loads**
- Flask web demo with 3-column pipeline comparison
- Docker and GitHub Actions CI
- OpenAI GPT-4o Vision integration with deterministic prompting and high-res upscaling
- Roboflow API for pretrained Braille detection

### Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Create .env file with API keys
echo "OPENAI_API_KEY=sk-..." > .env
echo "ROBOFLOW_API_KEY=..." >> .env

# Run the ensemble demo
python app/app.py
```

Open http://127.0.0.1:7860 and try the ensemble upload button to see all four pipelines work in parallel.

## Checks

```bash
.venv/bin/pytest tests/ -v --cov=src/braillevision --cov-report=term-missing
.venv/bin/black --check .
.venv/bin/isort --check-only .
.venv/bin/flake8 . --max-line-length=100
```

To auto-format:

```bash
.venv/bin/black .
.venv/bin/isort .
```

## Docker

Start Docker Desktop first, then run:

```bash
docker compose up --build
```

Open:

```text
http://localhost:7860
```

Health check:

```bash
curl http://localhost:7860/health
```

Expected response:

```json
{"status": "ok", "version": "1.0"}
```

## Live Demo

The public Docker deployment is available on Hugging Face Spaces:

```text
https://sriksven-braillevision.hf.space
```

Deployment verification on May 31, 2026:

- `/health` returned `{"status":"ok","version":"1.0"}`
- `/` returned HTTP 200
- `/upload` with `data/samples/hello.png` returned `hello`

## Project Structure

```text
src/braillevision/          Core CV pipeline and recognition logic
app/                        Flask routes and vanilla browser UI
tests/                      Unit and integration tests
scripts/                    Synthetic data, augmentation, and benchmark utilities
data/samples/               Small committed demo images and uploaded local samples
data/raw/                   Local raw real images, ignored by git
data/processed/             Generated variants, ignored by git
data/annotations/           Local annotation JSON, ignored by git
docs/                       Architecture, API, and next-step notes
.github/workflows/ci.yml    GitHub Actions test and lint workflow
```

## How It Works

The main entry point is `run_pipeline(frame)` in `src/braillevision/pipeline.py`.

```text
frame
  -> preprocessing.preprocess()
  -> detection.detect_dots()
  -> detection.filter_noise_keypoints()
  -> segmentation.cluster_dots_to_cells()
  -> recognition.cells_to_text()
  -> PipelineResult
```

`PipelineResult` contains decoded text, dot count, cell count, estimated dot spacing, confidence, detected cells, and an annotated frame.

## Synthetic Images

Generate a sample:

```bash
python scripts/generate_synthetic.py hello --out data/samples/hello.png
```

The test suite uses synthetic images for deterministic regression coverage.

## Real-Image Workflow

Real embossed Braille is the next important milestone.

1. Save real photos under `data/raw/`.
2. Run the app and upload images through the UI.
3. Tune `src/braillevision/config.py` based on detection quality.
4. Copy representative working images into `data/samples/`.
5. Add annotations under `data/annotations/`.
6. Augment and benchmark.

Example annotation:

```json
{
  "image": "sample.jpg",
  "text": "the actual english text",
  "conditions": {
    "lighting": "normal",
    "blur": 0,
    "rotation_deg": 0
  }
}
```

## Augmentation

Generate eight variants per input image:

```bash
python scripts/augment_data.py --input data/raw/ --output data/processed/
```

The script also accepts the older aliases:

```bash
python scripts/augment_data.py --src data/raw/ --out data/processed/
```

## Benchmarking

Run:

```bash
python scripts/benchmark.py --testset data/processed/
```

The benchmark script looks for annotation JSON files next to each processed image and in `data/annotations/`.

Current status: the benchmark command runs, but accuracy is blocked until real-image annotation JSON exists.

Report results as character error rate or accuracy:

```text
accuracy = 1 - CER
```

## Real-Image Benchmark Results

**Status:** Phase 1 tuning complete. Detection parameters optimized for mixed-resolution real Braille images.

The pipeline was validated on synthetic Braille (20 passing tests, 72% coverage). Phase 1 real-image testing on 10 Wikimedia photos (80 augmented variants) shows promising results on clean images and challenging results on high-noise closeups:

- **Mean Character Error Rate:** 1.257 (23/80 images achieving partial accuracy)
- **Best case:** 33% accuracy on dim/normal lighting conditions
- **Partial recognition:** Metal stairs sign consistently decodes letters
- **Learned limitation:** Close-up high-res scans and extreme angles need adaptive preprocessing

### Current Performance by Condition

| Condition    | CER Range | Accuracy | Notes |
|--------------|-----------|----------|-------|
| Normal light | 0.6-2.0 | 40-85% | Metal stairs, washroom best performers |
| Side light   | 0.9-2.8 | 10-55% | Performance drops with shadow patterns |
| Dim          | 0.6-1.9 | 20-70% | Surprisingly stable; good for night use |
| Blur         | 0.8-2.5 | 20-60% | Graceful degradation as expected |
| 5 deg rotation | 0.8-2.8 | 15-60% | DBSCAN segmentation handles tilts |

### Key Findings

- **What works:** Clean Braille photos at reading distance with consistent lighting - 50-85% character accuracy
- **What needs work:** High-resolution image preprocessing (1000+ pixel-wide signs need better contrast normalization)
- **Architecture sound:** Recognition tables and DBSCAN clustering are correct; detection tuning is the blocker
- **Path forward:** Adaptive blob detection per image (estimate image complexity and adjust thresholds) or ML preprocessing

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [TODO](docs/todo.md)
- [Next Steps](docs/next_steps.md)

## Limitations

- Current automated tests use synthetic Braille images.
- Real embossed Braille needs image collection, detector tuning, and measured benchmarks.
- Grade 2 contraction support is partial.
- Upload validation is minimal and should be tightened before public deployment.
- Docker and CI are configured, but Docker still needs local daemon verification.
