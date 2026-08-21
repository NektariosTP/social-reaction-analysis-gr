from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class IndicatorRow:
    region_code: str          # canonical periphery English name, or 'GR'
    indicator: str
    period: str
    value: float
    unit: str | None
    source: str               # 'eurostat' | 'worldbank'
    source_url: str
    released_at: date | None = None
