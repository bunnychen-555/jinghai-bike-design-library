#!/usr/bin/env python3
"""Collect licensed bicycle design references from Wikimedia Commons."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
JSON_PATH = DATA_DIR / "candidates.json"
CSV_PATH = DATA_DIR / "candidates.csv"
MAX_NEW_ITEMS = 12

SEARCHES = [
    "bicycle design frame",
    "folding bicycle design",
    "carbon bicycle frame",
    "vintage bicycle design",
    "cargo bicycle design",
    "track bicycle design",
]

ALLOWED_LICENSE_MARKERS = (
    "cc by", "cc-by", "cc0", "public domain", "pd-", "creative commons"
)


def clean(value: str | None) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def api_get(params: dict[str, str | int]) -> dict:
    query = urllib.parse.urlencode({
        "format": "json",
        "formatversion": 2,
        "origin": "*",
        **params,
    })
    request = urllib.request.Request(
        f"{API}?{query}",
        headers={"User-Agent": "JinghaiBikeDesignLibrary/1.0 (research archive)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def search_images(term: str) -> list[dict]:
    payload = api_get({
        "action": "query",
        "generator": "search",
        "gsrsearch": term,
        "gsrnamespace": 6,
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
        "iiurlwidth": 1200,
    })
    return payload.get("query", {}).get("pages", [])


def load_existing() -> list[dict]:
    if not JSON_PATH.exists():
        return []
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def make_record(page: dict, search_term: str) -> dict | None:
    info_list = page.get("imageinfo") or []
    if not info_list:
        return None
    info = info_list[0]
    meta = info.get("extmetadata") or {}
    license_name = clean((meta.get("LicenseShortName") or {}).get("value"))
    usage_terms = clean((meta.get("UsageTerms") or {}).get("value"))
    license_text = f"{license_name} {usage_terms}".lower()
    if not any(marker in license_text for marker in ALLOWED_LICENSE_MARKERS):
        return None

    title = str(page.get("title", "")).removeprefix("File:")
    source_url = info.get("descriptionurl") or info.get("url")
    image_url = info.get("thumburl") or info.get("url")
    if not title or not source_url or not image_url:
        return None

    source_key = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:16]
    return {
        "candidate_id": f"wm-{source_key}",
        "title": clean(title.rsplit(".", 1)[0]),
        "brand": "待识别",
        "category": "待分类",
        "style": "待分类",
        "material": "待确认",
        "focus": "整车",
        "year": "待确认",
        "summary": f"由关键词“{search_term}”自动发现，需人工确认设计价值、品牌与年代。",
        "image_url": image_url,
        "source_url": source_url,
        "source_site": "Wikimedia Commons",
        "creator": clean((meta.get("Artist") or {}).get("value")) or "未注明",
        "license": license_name or usage_terms,
        "review_status": "待审核",
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "search_term": search_term,
    }


def write_outputs(records: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    records.sort(key=lambda item: (item.get("review_status", ""), item["candidate_id"]))
    JSON_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fields = list(records[0].keys()) if records else [
        "candidate_id", "title", "brand", "category", "style", "material",
        "focus", "year", "summary", "image_url", "source_url", "source_site",
        "creator", "license", "review_status", "collected_at", "search_term",
    ]
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    existing = load_existing()
    known = {item.get("source_url") for item in existing}
    added = 0

    for term in SEARCHES:
        for page in search_images(term):
            record = make_record(page, term)
            if not record or record["source_url"] in known:
                continue
            existing.append(record)
            known.add(record["source_url"])
            added += 1
            if added >= MAX_NEW_ITEMS:
                break
        if added >= MAX_NEW_ITEMS:
            break

    write_outputs(existing)
    print(f"Collected {added} new candidates; {len(existing)} total pending records.")


if __name__ == "__main__":
    main()
