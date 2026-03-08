# WhatsApp Transcriber API

FastAPI service that transcribes `.ogg` audio files (for example, exported WhatsApp voice notes) using [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper).

## Features

- Transcribe all `.ogg` files from `input_audios/`
- Save transcriptions as `.txt` in `transcriptions/`
- REST API with FastAPI
- Auto-generated API docs (Swagger/ReDoc)
- Docker support (`Dockerfile` + `docker-compose.yml`)
- Pytest test suite

---

## Project Structure

```text
whatsapp-transcriber/
├── main.py
├── test_main.py
├── pytest.ini
├── Dockerfile
├── docker-compose.yml
├── input_audios/        # local input audios (gitignored)
├── transcriptions/      # output txt files (gitignored)
└── .gitignore
```

---

## Requirements

- Python 3.12+
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

2. Install dependencies:

   ```bash
   uv pip install fastapi "uvicorn[standard]" faster-whisper pytest httpx
   ```

3. Run API:

   ```bash
   uvicorn main:app --reload
   ```

4. Open docs:
   - Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

---

## API Endpoints

### `GET /health`

Health check.

**Response**

```json
{ "status": "ok" }
```

### `POST /transcribe-all`

Transcribes all `.ogg` files from `input_audios/`.

**Request body**

```json
{
  "language": "es",
  "vad_filter": true
}
```

**Response body**

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

## How It Works

- The API scans `input_audios/*.ogg`
- Loads Whisper model once (singleton in memory)
- Transcribes each file
- Writes text result to `transcriptions/<audio_name>.txt`
- Returns structured JSON with processed files

---

## Run Tests

```bash
pytest
```

Optional:

```bash
pytest -v
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
docker compose up --build
```

---

## Notes

- Put your `.ogg` files inside `input_audios/`.
- Output files are generated in `transcriptions/`.
- `input_audios/` and `transcriptions/` are intentionally gitignored.
- Use `--reload` only for development.
