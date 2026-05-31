# BrailleVision TODO

Status date: May 31, 2026

Work top to bottom. Do not skip the real-image tuning phase.

## Legend

- Done: completed locally
- Not done: still needs work
- Blocked: cannot proceed until an external condition changes

## 1. Environment Setup

Status: done.

- Done: virtual environment created with Python 3.11.7
- Done: `requirements-dev.txt` installed
- Done: project installed in editable mode with `pip install -e .`
- Done: OpenCV 4.13.0 confirmed installed
- Done: 20 tests passing with real OpenCV backend
- Done: coverage at 72%

## 2. Code Quality

Status: done.

- Done: `black .`
- Done: `isort .`
- Done: `flake8 . --max-line-length=100`
- Done: `setup.cfg` configured with flake8 excludes and isort `profile = black`

## 3. Scripts

Status: done.

- Done: `augment_data.py` accepts `--input` and `--output`
- Done: `augment_data.py` generates eight variants per image
- Done: `benchmark.py` reads sidecar JSON or files in `data/annotations/`

## 4. GitHub Repository

Status: not done.

Done when the public GitHub repo has a green CI badge.

Tasks:

- Create public GitHub repo named `braillevision`
- Add remote and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/braillevision
git branch -M main
git push -u origin main
```

- Confirm GitHub Actions starts under the Actions tab
- Wait for CI to pass
- Fix anything CI flags
- Add CI badge to `README.md`
- Commit and push README update:

```bash
git add README.md
git commit -m "docs: add CI badge"
git push
```

## 5. Docker

Status: blocked until Docker Desktop/daemon is running.

Done when the app runs cleanly inside Docker and health check passes.

Tasks:

- Open Docker Desktop and wait for it to fully start
- Verify daemon:

```bash
docker info
```

- Build and run:

```bash
docker compose up --build
```

- Open `http://localhost:7860`
- Check health:

```bash
curl http://localhost:7860/health
```

Expected:

```json
{"status": "ok", "version": "1.0"}
```

- Upload a test image through the UI inside Docker
- Stop container:

```bash
docker compose down
```

## 6. Real Braille Images

Status: not done. This is the highest-priority remaining product work.

Done when uploading a real Braille photo via the UI produces correct or near-correct English text.

### 6a. Collect Images

- Search for real physical Braille images:
  - `braille paper embossed close up camera`
  - `braille book page`
  - `braille label`
  - `braille sign`
- Download 20 to 30 real photos
- Save them to `data/raw/`

### 6b. Test In The App

```bash
source .venv/bin/activate
python app/app.py
```

Open:

```text
http://127.0.0.1:7860
```

Upload each image and record:

- expected text
- actual pipeline output
- dot count
- cell count
- confidence
- failure mode

### 6c. Tune `src/braillevision/config.py`

Change one value at a time, re-upload, and repeat.

- Dots not detected: lower `blob_min_area`
- Noise detected as dots: raise `blob_min_area` or lower `blob_max_area`
- Embossed dots look elongated: lower `blob_min_circularity` toward `0.4`
- Faint dots: raise `clahe_clip_limit` to `4.0` or `5.0`
- Light dots on dark paper: confirm invert fallback in `detection.py`
- Wrong cell grouping: check `estimate_dot_spacing`; typical webcam images should often be around 15 to 40 px

### 6d. Build Annotated Test Set

- Pick 10 real images where detection works reasonably well
- Copy them to `data/samples/`
- Create JSON files in `data/annotations/`

Example:

```json
{
  "image": "filename.jpg",
  "text": "actual english text here",
  "conditions": {
    "lighting": "normal",
    "blur": 0,
    "rotation_deg": 0
  }
}
```

## 7. Augmentation

Status: not done for real images.

Done when `data/processed/` has at least 80 images from 10 real images and eight variants each.

Run:

```bash
python scripts/augment_data.py --input data/raw/ --output data/processed/
```

Then spot-check outputs. They should look like realistic degraded images, not broken samples.

## 8. Benchmark

Status: not done.

Done when README has a benchmark table with real numbers.

Run:

```bash
python scripts/benchmark.py --testset data/processed/
```

Record accuracy by condition:

- normal
- dim
- side light
- blur
- rotation

Use this table shape in `README.md`:

```markdown
| Condition    | Accuracy |
|--------------|----------|
| Normal       | XX%      |
| Side light   | XX%      |
| Dim          | XX%      |
| Blur         | XX%      |
| 5 deg rotate | XX%      |
```

Do not claim high accuracy without a number.

## 9. Hugging Face Spaces Deployment

Status: not done.

Done when a public URL exists that anyone can open and use.

Tasks:

- Create Hugging Face account if needed
- Create new Space:
  - Space name: `braillevision`
  - SDK: Docker
  - Hardware: CPU Basic
  - Visibility: Public
- Add remote:

```bash
git remote add hf https://huggingface.co/spaces/YOUR_HF_USERNAME/braillevision
```

- Push:

```bash
git push hf main
```

- Watch build logs
- Confirm live URL works
- Upload an image and test text output/TTS

## 10. README Completion

Status: partially done.

Done when README has live URL, demo GIF, quick start, Docker instructions, and real benchmark numbers.

Tasks:

- Add live demo link near top:

```markdown
**[Live Demo](https://YOUR_HF_USERNAME-braillevision.hf.space)**
```

- Record 30 to 60 second app demo
- Convert to GIF:

```bash
ffmpeg -i demo.mov -vf fps=10,scale=800:-1 docs/demo.gif
```

- Add GIF below title:

```markdown
![BrailleVision demo](docs/demo.gif)
```

- Add benchmark table from step 8
- Verify quick start from a clean clone

Recommended README order:

1. Title and one-line description
2. Badges
3. Live demo link
4. Demo GIF
5. How it works
6. Quick start
7. Docker
8. Benchmark results
9. Project structure
10. License

## 11. Demo Video

Status: not done.

Done when video is under 3 minutes, includes TTS audio, and has a shareable URL.

Record:

- 15s: show Braille image
- 30s: show detection overlay
- 20s: show text in UI
- 15s: press TTS and let audio play
- 30s: upload a different image
- 20s: change lighting or show confidence drop honestly

Then:

- Watch it back
- Confirm audio is audible
- Confirm text is readable
- Upload to YouTube unlisted or Google Drive

## 12. Devpost Submissions

Status: not done.

Done when every submission is submitted, not draft.

Problem summary:

Braille is essential for visually impaired users, but many caregivers and teachers cannot read it tactilely. Existing tools often convert Unicode Braille symbols, but they do not process real camera images of physical embossed paper. This creates an accessibility gap.

Solution summary:

BrailleVision is a computer-vision pipeline that accepts live webcam frames or uploaded images of physical Braille and outputs English text with speech. It uses CLAHE preprocessing for lighting robustness, dot detection for Braille extraction, geometry-based segmentation for cells, and Braille lookup tables for recognition.

Mention:

- CLAHE preprocessing
- dot detection
- segmentation
- perspective correction
- Grade 1 recognition
- partial Grade 2 support
- real-time MJPEG stream
- GitHub Actions CI
- Docker deployment

Avoid claiming 90%+ accuracy until real-image benchmarks prove it.

## 13. Final Pre-Deadline Check

- GitHub repo is public
- CI is green on main
- Hugging Face Spaces URL loads
- Demo video URL is accessible
- Devpost submissions are submitted
- README GIF loads on GitHub
- Live demo link works
- Quick start works from a fresh clone

## Known Issues

| Issue | Priority | Action |
|-------|----------|--------|
| Tests use synthetic images only | High | Real-image tuning |
| Docker not tested locally | High | Start Docker Desktop |
| Grade 2 contraction support partial | Medium | Improve if time allows |
| Upload validation minimal | Medium | Add file size and type checks |
| UI keyboard navigation incomplete | Low | Polish after core demo |

## Priority Order

| # | Step | Why |
|---|------|-----|
| 1 | Push to GitHub | Enables public repo and CI |
| 2 | Verify Docker | Required for Hugging Face Spaces |
| 3 | Real images and tuning | Proves the product works |
| 4 | Deploy to Hugging Face Spaces | Provides public demo URL |
| 5 | Record demo video | Required for submissions |
| 6 | Benchmark and README GIF | Improves judge confidence |
| 7 | Submit Devpost entries | Final deliverable |

