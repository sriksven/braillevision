# API

The Flask app lives in `app/app.py`.

## `GET /`

Serves the browser interface from `app/templates/index.html`.

Response type: `text/html`

## `GET /video_feed`

Returns an MJPEG stream of annotated frames.

Response type:

```text
multipart/x-mixed-replace; boundary=frame
```

The stream uses the latest annotated frame produced by the demo worker or upload handler.

## `GET /result`

Returns the latest pipeline result as JSON.

Example:

```json
{
  "text": "hello",
  "dot_count": 14,
  "cell_count": 5,
  "confidence": 1.0,
  "spacing": 22.0
}
```

Fields:

- `text`: decoded text
- `dot_count`: number of detected dots after filtering
- `cell_count`: number of segmented Braille cells
- `confidence`: fraction of cells decoded to known characters
- `spacing`: estimated within-cell dot spacing in pixels

When no result exists yet:

```json
{
  "text": "",
  "dot_count": 0,
  "cell_count": 0,
  "confidence": 0.0,
  "spacing": 0.0
}
```

## `POST /upload`

Accepts multipart form data with an `image` field.

Example:

```bash
curl -F "image=@data/samples/hello.png" http://127.0.0.1:7860/upload
```

Response:

```json
{
  "text": "hello",
  "dot_count": 14,
  "cell_count": 5,
  "confidence": 1.0,
  "spacing": 22.0,
  "annotated_image_b64": "data:image/jpeg;base64,..."
}
```

Current behavior:

- Saves the uploaded image into `data/samples/`.
- Runs the pipeline once.
- Updates the latest server-side result.
- Returns an annotated JPEG data URL.

Current limitations:

- File size is not limited.
- MIME/type validation is minimal.
- Uploaded files are kept in `data/samples/`.

## `GET /health`

Health check for local development, Docker, and deployment probes.

Example:

```bash
curl http://127.0.0.1:7860/health
```

Response:

```json
{"status": "ok", "version": "1.0"}
```

