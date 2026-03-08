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
    language: str = "es"
    vad_filter: bool = True


class FileResult(BaseModel):
    file: str
    output: str
    detected_language: str


class TranscribeResponse(BaseModel):
    processed: int
    results: List[FileResult]


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        print("Loading model...")
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe_all(language: str = "es", vad_filter: bool = True) -> list[FileResult]:
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
    return {"status": "ok"}


@app.post("/transcribe-all", response_model=TranscribeResponse)
def transcribe_endpoint(payload: TranscribeRequest):
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
