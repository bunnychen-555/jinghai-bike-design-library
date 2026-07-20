#!/usr/bin/env python3
"""Send collected bicycle candidates to the Google Sheets Apps Script endpoint."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "candidates.json"


def main() -> None:
    endpoint = os.environ.get("GOOGLE_SCRIPT_URL", "").strip()
    token = os.environ.get("GOOGLE_INGEST_TOKEN", "").strip()

    if not endpoint or not token:
        raise SystemExit("Missing GOOGLE_SCRIPT_URL or GOOGLE_INGEST_TOKEN")

    records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    payload = json.dumps(
        {"token": token, "records": records},
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode("utf-8")
        print(body)

    result = json.loads(body)
    if not result.get("ok"):
        raise SystemExit(f"Google Sheets sync failed: {result}")

    print(
        f"Google Sheets sync complete: "
        f"{result.get('added', 0)} added, {result.get('skipped', 0)} skipped."
    )


if __name__ == "__main__":
    main()
