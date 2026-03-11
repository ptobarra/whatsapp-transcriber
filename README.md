# WhatsApp Transcriber API

FastAPI service that transcribes `.ogg` audio files (for example, exported WhatsApp voice notes) using [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper).

## Features

- Transcribe all `.ogg` files from `input_audios/`
- Save transcriptions as `.txt` in `transcriptions/`
- REST API with FastAPI
- CLI helper to trigger `POST /transcribe-all`
- Auto-generated API docs (Swagger/ReDoc)
- Docker support (`Dockerfile` + `docker-compose.yaml`)
- Pytest test suite

---

## Project Structure

```text
whatsapp-transcriber/
├── main.py
├── send_transcribe_all.py
├── test_main.py
├── test_send_transcribe_all.py
├── pyproject.toml
├── uv.lock
├── pytest.ini
├── Dockerfile
├── docker-compose.yaml
├── input_audios/        # local input audios (gitignored)
├── transcriptions/      # output txt files (gitignored)
└── .gitignore
```

---

## Requirements

- Python 3.11+
- `uv` (recommended) or `pip`
- `ffmpeg` (required by whisper audio decoding)
- Optional: Docker Desktop + WSL integration

---

## Local Setup (uv + virtualenv)

1. Create and activate virtual environment:

   ```bash
   cd /home/ptobarra/projects/whatsapp-transcriber
   uv venv .venv
   source .venv/bin/activate
   ```

2. Install project and development dependencies from pyproject.toml and uv.lock:

   ```bash
   uv sync --active --dev
   ```

3. Run API:

   ```bash
   uv run uvicorn main:app --reload
   ```

4. Open docs:
   - Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

---

## API Endpoints

### `GET /health`

Health check.

RESPONSE

```json
{ "status": "ok" }
```

### `POST /transcribe-all`

Transcribes all `.ogg` files from `input_audios/`.

REQUEST BOY

```json
{
  "language": "es",
  "vad_filter": true
}
```

RESPONSE BODY

```json
{
  "processed": 1,
  "results": [
    {
      "file": "audio_001.ogg",
      "output": "audio_001.txt",
      "detected_language": "es"
    }
  ]
}
```

---

## CLI Client

You can trigger the transcription endpoint from the command line with:

```bash
python send_transcribe_all.py --language en
python send_transcribe_all.py --no-vad-filter
python send_transcribe_all.py --base-url http://127.0.0.1:8000
```

---

## How It Works

- The API scans `input_audios/*.ogg`
- Loads Whisper model once (singleton in memory)
- Transcribes each file
- Writes text result to `transcriptions/<audio_name>.txt`
- Returns structured JSON with processed files

---

## Run Tests

Run the full suite:

```bash
pytest
```

Optional:

```bash
pytest -v
```

Run only the API tests:

```bash
pytest -v test_main.py
```

Run only the CLI client tests:

```bash
pytest -v test_send_transcribe_all.py
```

---

## Docker

Build and run with Docker:

```bash
docker build -t whatsapp-transcriber .
docker run --rm -p 8000:8000 \
  -v "$(pwd)/input_audios:/app/input_audios" \
  -v "$(pwd)/transcriptions:/app/transcriptions" \
  whatsapp-transcriber
```

Or with Compose:

```bash
docker compose up --build api
```

---

## Notes

- Put your `.ogg` files inside `input_audios/`.
- Output files are generated in `transcriptions/`.
- `input_audios/` and `transcriptions/` are intentionally gitignored.
- Use `--reload` only for development.
