from __future__ import annotations
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import numpy as np
import pytest
from nlp import pipeline as P
from nlp.clustering import ClusterResult

def _vec_literal():
    return "[" + ",".join(["0.1"] * 768) + "]"

@pytest.mark.asyncio
async def test_pipeline_fetches_body_text_for_day_resolution(monkeypatch):
    v = np.full(768, 0.1, dtype=np.float32)
    cluster = {0: ClusterResult(article_ids=["a", "b"], embeddings=np.array([v, v]),
                                  centroid=v, intra_sim=1.0)}

    async def fake_embed(session): return 0
    async def fake_cluster(session, **kw): return cluster
    async def fake_assign(session, *, centroid, article_ids, threshold): return "evt-x"
    async def fake_load(session): return []
    async def fake_apply(session, merges): return 0
    async def fake_gate(session): return 0

    monkeypatch.setattr(P, "embed_articles", fake_embed)
    monkeypatch.setattr(P, "single_pass_cluster_from_db", fake_cluster)
    monkeypatch.setattr(P, "assign_event_id", fake_assign)
    monkeypatch.setattr(P, "load_existing_events", fake_load)
    monkeypatch.setattr(P, "find_merges", lambda *a, **k: [])
    monkeypatch.setattr(P, "apply_merges", fake_apply)
    monkeypatch.setattr(P, "_gate_detected_events", fake_gate)
    monkeypatch.setattr(P, "find_duplicates_global", lambda *a, **k: set())
    monkeypatch.setattr(P, "mark_duplicates", AsyncMock(return_value=0))

    executed: list[str] = []
    t = datetime(2026, 9, 14, tzinfo=timezone.utc)

    def result(rows):
        r = MagicMock(); r.all.return_value = rows; return r

    async def fake_execute(query, params=None):
        sql = query.text
        executed.append(sql)
        if "body_text" in sql:  # per-cluster meta fetch
            return result([("a", "Απεργία στις 16/9", "body", t),
                           ("b", "Στάση εργασίας 16/9", "body", t)])
        if "embedding::text" in sql:  # window dedup fetch
            return result([("a", _vec_literal(), t), ("b", _vec_literal(), t)])
        return result([])

    session = MagicMock()
    session.execute = AsyncMock(side_effect=fake_execute)
    session.commit = AsyncMock()

    class FakeFactory:
        def __call__(self):
            cm = MagicMock()
            cm.__aenter__ = AsyncMock(return_value=session)
            cm.__aexit__ = AsyncMock(return_value=False)
            return cm

    monkeypatch.setattr(P, "async_sessionmaker", lambda *a, **k: FakeFactory())
    monkeypatch.setattr(P, "create_async_engine", lambda url: MagicMock(dispose=AsyncMock()))

    metrics = await P.run_nlp_pipeline()
    assert any("body_text" in s for s in executed)  # new day-resolution fetch runs
    assert metrics["n_events"] >= 1
