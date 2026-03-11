#!/usr/bin/env python3
"""CLI client for the WhatsApp Transcriber FastAPI service.

This script sends a `POST /transcribe-all` request to the API and prints the
JSON response in a readable format.

Defaults:
- Base URL: http://127.0.0.1:8000
- Language: es
- VAD filter: enabled

Exit codes:
- 0: request succeeded
- 1: HTTP or connection error
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


def main() -> int:
    """Parse CLI arguments, call `POST /transcribe-all`, and print the response.

    Returns:
        int: Process exit code (`0` on success, `1` on HTTP/connection failures).
    """
    parser = argparse.ArgumentParser(
        description="Send POST /transcribe-all to the WhatsApp Transcriber API"
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the API server.",
    )
    parser.add_argument(
        "--language",
        default="es",
        help="Language hint for transcription (e.g. 'es', 'en').",
    )
    parser.add_argument(
        "--vad-filter",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable voice activity detection filter (use --no-vad-filter to disable).",
    )
    args = parser.parse_args()

    url = f"{args.base_url.rstrip('/')}/transcribe-all"
    payload = {"language": args.language, "vad_filter": args.vad_filter}
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read().decode("utf-8")
            print(f"HTTP {resp.status}")
            print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
            return 0
    except urllib.error.HTTPError as e:
        print(
            f"HTTP error {e.code}: {e.read().decode('utf-8', errors='replace')}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
