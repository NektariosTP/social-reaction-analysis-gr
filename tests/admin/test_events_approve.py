import pytest
from unittest.mock import AsyncMock, MagicMock

from admin.routes.events import approve_event


@pytest.mark.asyncio
async def test_approve_routes_all_detected_to_approved():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())
    session.commit = AsyncMock()
    resp = await approve_event("evt-1", session=session)
    sql = session.execute.call_args.args[0].text
    assert "SET status = 'approved'" in sql
    assert "'announced'" not in sql
    assert "WHERE id = :id AND status = 'detected'" in sql
    assert resp.status_code == 303
