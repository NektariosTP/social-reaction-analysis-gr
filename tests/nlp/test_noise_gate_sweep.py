"""Noise-gate sweep over freshly detected events."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_gate_rejects_low_score_events() -> None:
    from nlp import pipeline

    session = MagicMock()
    detected = MagicMock()
    detected.all.return_value = [
        ("aaaaaaaa-0000-0000-0000-000000000000",),
        ("bbbbbbbb-0000-0000-0000-000000000000",),
    ]
    arts = MagicMock()
    arts.all.return_value = [("κάποιος τίτλος", "σώμα")]
    # 1st call: list detected; then per event: fetch articles, then UPDATE
    session.execute = AsyncMock(side_effect=[detected, arts, MagicMock(), arts, MagicMock()])

    with patch("nlp.pipeline.noise_gate_score", side_effect=[0.1, 0.9]), \
         patch("nlp.pipeline.NOISE_GATE_THRESHOLD", 0.55):
        n = await pipeline._gate_detected_events(session)

    assert n == 1  # only the 0.1 event rejected
    executed = " ".join(str(c.args[0]) for c in session.execute.call_args_list)
    assert "status = 'rejected'" in executed
