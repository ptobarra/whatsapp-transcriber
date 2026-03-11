"""FastAPI service to transcribe WhatsApp `.ogg` audio files with Faster-Whisper.

The service scans `input_audios/`, transcribes each `.ogg` file, writes output
text files to `transcriptions/`, and exposes endpoints to trigger batch
transcription and check service health.
"""

from pathlib import Path
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from faster_whisper import WhisperModel

# Folder containing the .ogg files
AUDIO_DIR = Path(r"input_audios")

# Output folder for transcriptions
OUTPUT_DIR = Path(r"transcriptions")
OUTPUT_DIR.mkdir(exist_ok=True)

# Model options:
# "small" = good balance of speed/quality
# "medium" = better quality, slower
# "large-v3" = best quality, much slower
MODEL_SIZE = "small"

app = FastAPI(title="WhatsApp Transcriber API", version="1.0.0")
_model: WhisperModel | None = None


class TranscribeRequest(BaseModel):
    """Request payload for `POST /transcribe-all`.

    Attributes:
        language: Language hint used by Whisper (for example, `"es"` or `"en"`).
        vad_filter: Enables voice activity detection to trim non-speech segments.
    """

    language: str = "es"
    vad_filter: bool = True


class FileResult(BaseModel):
    """Transcription metadata for one processed audio file.

    Attributes:
        file: Input audio filename.
        output: Generated output text filename.
        detected_language: Language detected by the model for this audio.
    """

    file: str
    output: str
    detected_language: str


class TranscribeResponse(BaseModel):
    """Response payload returned by `POST /transcribe-all`.

    Attributes:
        processed: Number of audio files processed.
        results: Per-file transcription metadata.
    """

    processed: int
    results: List[FileResult]


def get_model() -> WhisperModel:
    """Return a singleton Whisper model instance.

    The model is loaded lazily on first use and then reused for subsequent
    requests to avoid repeated initialization overhead.
    """
    global _model
    if _model is None:
        print("Loading model...")
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe_all(language: str = "es", vad_filter: bool = True) -> list[FileResult]:
    """Transcribe all `.ogg` files in `AUDIO_DIR` and write `.txt` outputs.

    Args:
        language: Language hint passed to Whisper transcription.
        vad_filter: Whether to enable voice activity detection filtering.

    Returns:
        list[FileResult]: Metadata for each processed file. Returns an empty
        list when no `.ogg` files are found.
    """
    model = get_model()
    audio_files = sorted(AUDIO_DIR.glob("*.ogg"))
    if not audio_files:
        print(f"No .ogg files found in: {AUDIO_DIR}")
        return []

    print(f"Found {len(audio_files)} audio files.")
    results: list[FileResult] = []
    for audio_path in audio_files:
        print(f"Transcribing: {audio_path.name}")

        segments, info = model.transcribe(
            str(audio_path), language=language, vad_filter=vad_filter
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()

        output_path = OUTPUT_DIR / f"{audio_path.stem}.txt"
        output_path.write_text(text, encoding="utf-8")

        print(f"Saved: {output_path.name} | Detected language: {info.language}")

        results.append(
            FileResult(
                file=audio_path.name,
                output=output_path.name,
                detected_language=info.language,
            )
        )

    print("Done.")

    return results


@app.get("/health")
def health():
    """Health-check endpoint used to verify the API is up."""
    return {"status": "ok"}


@app.post("/transcribe-all", response_model=TranscribeResponse)
def transcribe_endpoint(payload: TranscribeRequest):
    """Run batch transcription for all input audios and return a summary.

    Args:
        payload: Transcription configuration received from the request body.

    Returns:
        TranscribeResponse: Processed file count and per-file result metadata.
    """
    results = transcribe_all(language=payload.language, vad_filter=payload.vad_filter)
    return TranscribeResponse(processed=len(results), results=results)


# def main():
#     print("Loading model...")
#     model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

#     audio_files = sorted(AUDIO_DIR.glob("*.ogg"))

#     if not audio_files:
#         print(f"No .ogg files found in: {AUDIO_DIR}")
#         return

#     print(f"Found {len(audio_files)} audio files.")

#     for audio_path in audio_files:
#         print(f"Transcribing: {audio_path.name}")

#         segments, info = model.transcribe(
#             str(audio_path), language="es", vad_filter=True
#         )

#         text = " ".join(segment.text.strip() for segment in segments).strip()

#         output_path = OUTPUT_DIR / f"{audio_path.stem}.txt"
#         output_path.write_text(text, encoding="utf-8")

#         print(f"Saved: {output_path.name} | Detected language: {info.language}")

#     print("Done.")


# if __name__ == "__main__":
#     main()
