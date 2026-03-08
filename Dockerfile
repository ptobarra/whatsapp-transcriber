FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Optional but recommended for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY main.py /app/main.py

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi "uvicorn[standard]" faster-whisper

# Ensure runtime folders exist
RUN mkdir -p /app/input_audios /app/transcriptions

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]