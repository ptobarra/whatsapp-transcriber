"""Tests for the CLI client that calls `POST /transcribe-all`."""

import io
import json
import urllib.error

from unittest.mock import patch

import send_transcribe_all


class _FakeResponse:
    """Simple context-manager response stub for `urllib.request.urlopen` tests."""

    def __init__(self, status: int, payload: dict):
        """Store HTTP status and JSON body payload."""
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        """Return encoded JSON response bytes."""
        return self._body

    def __enter__(self):
        """Support use in `with` statements."""
        return self

    def __exit__(self, exc_type, exc, tb):
        """Do not suppress exceptions raised inside the context."""
        return False


def test_main_success_default_args(capsys):
    """Return `0` and print formatted response when call succeeds with defaults."""
    fake_response = _FakeResponse(
        200,
        {
            "processed": 1,
            "results": [
                {
                    "file": "a.ogg",
                    "output": "a.txt",
                    "detected_language": "es",
                }
            ],
        },
    )

    with (
        patch("sys.argv", ["send_transcribe_all.py"]),
        patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen,
    ):
        rc = send_transcribe_all.main()

    assert rc == 0

    out = capsys.readouterr().out
    assert "HTTP 200" in out
    assert '"processed": 1' in out

    # Validate request details sent to urlopen
    req = mock_urlopen.call_args.args[0]
    timeout = mock_urlopen.call_args.kwargs["timeout"]

    assert timeout == 300
    assert req.full_url == "http://127.0.0.1:8000/transcribe-all"
    assert req.get_method() == "POST"
    assert req.headers["Content-type"] == "application/json"

    payload = json.loads(req.data.decode("utf-8"))
    assert payload == {"language": "es", "vad_filter": True}


def test_main_success_custom_args_and_no_vad():
    """Build request from custom CLI args and disable VAD when requested."""
    fake_response = _FakeResponse(200, {"processed": 0, "results": []})

    with (
        patch(
            "sys.argv",
            [
                "send_transcribe_all.py",
                "--base-url",
                "http://localhost:9000/",
                "--language",
                "en",
                "--no-vad-filter",
            ],
        ),
        patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen,
    ):
        rc = send_transcribe_all.main()

    assert rc == 0
    req = mock_urlopen.call_args.args[0]
    payload = json.loads(req.data.decode("utf-8"))

    assert req.full_url == "http://localhost:9000/transcribe-all"
    assert payload == {"language": "en", "vad_filter": False}


def test_main_http_error_returns_1_and_prints_stderr(capsys):
    """Return `1` and print details when server responds with HTTP error."""
    http_error = urllib.error.HTTPError(
        url="http://127.0.0.1:8000/transcribe-all",
        code=500,
        msg="Internal Server Error",
        hdrs=None,
        fp=io.BytesIO(b'{"detail":"boom"}'),
    )

    with (
        patch("sys.argv", ["send_transcribe_all.py"]),
        patch("urllib.request.urlopen", side_effect=http_error),
    ):
        rc = send_transcribe_all.main()

    assert rc == 1
    err = capsys.readouterr().err
    assert "HTTP error 500" in err
    assert "boom" in err


def test_main_url_error_returns_1_and_prints_stderr(capsys):
    """Return `1` and print connection error when request cannot be made."""
    with (
        patch("sys.argv", ["send_transcribe_all.py"]),
        patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ),
    ):
        rc = send_transcribe_all.main()

    assert rc == 1
    err = capsys.readouterr().err
    assert "Connection error" in err
