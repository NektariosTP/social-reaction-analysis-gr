from unittest.mock import AsyncMock, MagicMock

import pytest

from api.routes.events import _fetch_events


@pytest.mark.asyncio
async def test_fetch_events_includes_announced_status_and_roster():
    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    await _fetch_events(session)
    sql = session.execute.call_args.args[0].text
    assert "status IN ('enriched', 'announced')" in sql
    assert "announced_by" in sql
    assert "participating_unions" in sql
    assert "array_agg" in sql.lower()
