from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient

import main
from main import app, get_model, transcribe_all, AUDIO_DIR, OUTPUT_DIR


@pytest.fixture(autouse=True)
def reset_model_cache():
    """Reset singleton model before/after each test."""
    main._model = None
    yield
    main._model = None


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_whisper_model():
    """Mock WhisperModel to avoid loading actual model"""
    with patch("main.WhisperModel") as mock_cls:
        mock_instance = Mock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def setup_test_dirs(tmp_path):
    """Create temporary directories for testing"""
    audio_dir = tmp_path / "input_audios"
    output_dir = tmp_path / "transcriptions"
    audio_dir.mkdir()
    output_dir.mkdir()

    with patch("main.AUDIO_DIR", audio_dir), patch("main.OUTPUT_DIR", output_dir):
        yield audio_dir, output_dir


def test_health_endpoint(client):
    """Test /health endpoint returns OK"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_transcribe_endpoint_no_files(client, setup_test_dirs, mock_whisper_model):
    """Test /transcribe-all with no audio files"""
    response = client.post(
        "/transcribe-all", json={"language": "es", "vad_filter": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 0
    assert data["results"] == []


def test_transcribe_endpoint_with_files(client, setup_test_dirs, mock_whisper_model):
    """Test /transcribe-all with audio files"""
    audio_dir, output_dir = setup_test_dirs

    # Create dummy audio file
    audio_file = audio_dir / "test_audio.ogg"
    audio_file.write_bytes(b"fake audio data")

    # Mock transcription result
    mock_segment = Mock()
    mock_segment.text = "Hola mundo"
    mock_info = Mock()
    mock_info.language = "es"
    mock_whisper_model.transcribe.return_value = ([mock_segment], mock_info)

    response = client.post(
        "/transcribe-all", json={"language": "es", "vad_filter": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["file"] == "test_audio.ogg"
    assert data["results"][0]["output"] == "test_audio.txt"
    assert data["results"][0]["detected_language"] == "es"

    # Verify transcription file was created
    output_file = output_dir / "test_audio.txt"
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == "Hola mundo"


def test_transcribe_endpoint_custom_params(client, setup_test_dirs, mock_whisper_model):
    """Test /transcribe-all with custom language and vad_filter"""
    audio_dir, output_dir = setup_test_dirs

    audio_file = audio_dir / "english_audio.ogg"
    audio_file.write_bytes(b"fake audio")

    mock_segment = Mock()
    mock_segment.text = "Hello world"
    mock_info = Mock()
    mock_info.language = "en"
    mock_whisper_model.transcribe.return_value = ([mock_segment], mock_info)

    response = client.post(
        "/transcribe-all", json={"language": "en", "vad_filter": False}
    )

    assert response.status_code == 200
    # Verify transcribe was called with correct params
    mock_whisper_model.transcribe.assert_called_once()
    call_args = mock_whisper_model.transcribe.call_args
    assert call_args.kwargs["language"] == "en"
    assert call_args.kwargs["vad_filter"] is False


def test_transcribe_all_multiple_files(setup_test_dirs, mock_whisper_model):
    """Test transcribe_all with multiple audio files"""
    audio_dir, output_dir = setup_test_dirs

    # Create multiple audio files
    for i in range(3):
        (audio_dir / f"audio_{i}.ogg").write_bytes(b"fake")

    mock_segment = Mock()
    mock_segment.text = "Test transcription"
    mock_info = Mock()
    mock_info.language = "es"
    mock_whisper_model.transcribe.return_value = ([mock_segment], mock_info)

    results = transcribe_all(language="es", vad_filter=True)

    assert len(results) == 3
    assert all(r.detected_language == "es" for r in results)
    assert mock_whisper_model.transcribe.call_count == 3


def test_transcribe_all_strips_whitespace(setup_test_dirs, mock_whisper_model):
    """Test that transcription strips and joins segments correctly"""
    audio_dir, output_dir = setup_test_dirs

    audio_file = audio_dir / "test.ogg"
    audio_file.write_bytes(b"fake")

    # Mock multiple segments with whitespace
    segments = [Mock(text="  Hello  "), Mock(text="  world  "), Mock(text="  test  ")]
    mock_info = Mock()
    mock_info.language = "en"
    mock_whisper_model.transcribe.return_value = (segments, mock_info)

    results = transcribe_all()

    output_file = output_dir / "test.txt"
    content = output_file.read_text(encoding="utf-8")
    assert content == "Hello world test"


def test_get_model_singleton():
    """Test that get_model returns the same instance"""
    with patch("main.WhisperModel") as mock_whisper:
        mock_instance = Mock()
        mock_whisper.return_value = mock_instance

        # Reset the global model
        import main

        main._model = None

        model1 = get_model()
        model2 = get_model()

        assert model1 is model2
        mock_whisper.assert_called_once()


def test_transcribe_request_defaults():
    """Test TranscribeRequest model defaults"""
    from main import TranscribeRequest

    request = TranscribeRequest()
    assert request.language == "es"
    assert request.vad_filter is True


def test_invalid_request_payload(client):
    """Test /transcribe-all with invalid payload"""
    response = client.post(
        "/transcribe-all", json={"language": "es", "vad_filter": "not_a_boolean"}
    )
    assert response.status_code == 422  # Validation error
