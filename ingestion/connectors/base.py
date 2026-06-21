"""Abstract base class for all ingestion source connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ingestion.models import RawDocument


class SourceConnector(ABC):
    @abstractmethod
    async def fetch(self) -> list[RawDocument]:
        """Fetch and return normalised documents from this source."""
