# Next Steps

Work through this list in order. The project already runs locally on synthetic images; the remaining work is about proving it on real Braille and preparing a public demo.

For the full checklist, see [TODO](todo.md).

## 1. Docker Verification

Done when `docker compose up --build` starts and `http://localhost:7860/health` returns OK.

```bash
docker compose up --build
curl http://localhost:7860/health
docker compose down
```

If Docker reports that it cannot connect to the daemon, start Docker Desktop and retry.

## 2. Real Braille Images

Done when uploading real Braille photos through the UI produces correct or near-correct text.

- Save 20 to 30 real photos in `data/raw/`.
- Try close-up embossed paper, Braille book pages, labels, and signs.
- Upload them through the app one by one.
- Record output text versus expected text.

Tune `src/braillevision/config.py` one value at a time:

- Lower `blob_min_area` if real dots are missed.
- Raise `blob_min_area` if noise is detected as dots.
- Lower `blob_min_circularity` if embossed dots appear elongated.
- Raise `clahe_clip_limit` if dots are too faint.
- Check `estimate_dot_spacing` output if cells are grouped incorrectly.

## 3. Annotated Test Set

Done when at least 10 real images have annotation JSON.

Example file in `data/annotations/`:

```json
{
  "image": "filename.jpg",
  "text": "the actual english text",
  "conditions": {
    "lighting": "normal",
    "blur": 0,
    "rotation_deg": 0
  }
}
```

## 4. Augmentation

Done when `data/processed/` contains variants for the real-image set.

```bash
python scripts/augment_data.py --input data/raw/ --output data/processed/
```

The script creates eight variants per image.

## 5. Benchmark

Done when README has a benchmark table with real numbers.

```bash
python scripts/benchmark.py --testset data/processed/
```

Record character error rate by condition and convert to accuracy:

```text
accuracy = 1 - CER
```

## 6. Public Repo and CI

Done when the GitHub repo is public and Actions is green.

- Push to GitHub.
- Confirm `.github/workflows/ci.yml` runs.
- Fix any CI-only failures.
- Add the CI badge to `README.md` after the first successful run.

## 7. Public Demo

Done when a public URL loads the app and accepts an uploaded image.

Recommended target:

- Hugging Face Spaces
- SDK: Docker
- Hardware: CPU Basic
- Visibility: Public

## 8. Demo Assets

Done when the README and submission have visible proof.

- Record a 30 to 60 second GIF for `docs/demo.gif`.
- Record a demo video under 3 minutes.
- Include TTS audio in the demo video.
- Show real image upload and text output.

## 9. Submission Notes

Be explicit and honest:

- Synthetic tests pass.
- Real-image accuracy depends on collected image conditions.
- Grade 2 support is partial.
- Upload validation is minimal.
- Report real benchmark numbers once available.
