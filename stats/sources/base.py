from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from stats.catalog import IndicatorSpec
from stats.models import IndicatorRow


class IndicatorSource(ABC):
    source_name: str

    @abstractmethod
    async def fetch(self, spec: IndicatorSpec, client: httpx.AsyncClient) -> list[IndicatorRow]:
        """Fetch all rows for one indicator spec."""
