"""Shared data contract for all ingestion connectors."""
from __future__ import annotations

import hashlib
from datetime import datetime

from pydantic import BaseModel, model_validator


class RawDocument(BaseModel):
    source_id: str
    source_type: str
    url: str
    canonical_url: str
    title: str
    body_text: str
    language: str
    published_at: datetime | None
    content_hash: str = ""

    @model_validator(mode="after")
    def _compute_hash(self) -> "RawDocument":
        if not self.content_hash:
            raw = self.canonical_url.strip() + "|" + self.title.strip().lower()
            self.content_hash = hashlib.sha256(raw.encode()).hexdigest()
        return self
