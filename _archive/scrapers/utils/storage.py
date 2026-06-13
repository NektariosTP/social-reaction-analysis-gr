"""
scrapers/utils/storage.py

Persistence helpers for scraper output.
Records are written as newline-delimited JSON (.ndjson) files.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from scrapers.config import OUTPUT_DIR

logger = logging.getLogger(__name__)


def save_records(records: list[dict], source_name: str) -> Path:
    """
    Append *records* to a date-stamped .ndjson file for the given source.

    File layout:
        data/raw/<source_name>/<YYYY-MM-DD>.ndjson

    Returns the path to the written file.
    """
    if not records:
        logger.info("[%s] No records to save.", source_name)
        return OUTPUT_DIR

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dest_dir = OUTPUT_DIR / source_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    filepath = dest_dir / f"{today}.ndjson"

    with filepath.open("a", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info("[%s] Saved %d records → %s", source_name, len(records), filepath)
    return filepath
