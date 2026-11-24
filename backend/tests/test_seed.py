"""IT-DB-003: running the seed twice gives the same number of rows.

Needs the local database (docker compose up -d db) with the tables
(alembic upgrade head). If it is not reachable the tests are skipped,
so they do not fail on a machine (or CI) without a database.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings
from app.db.seed import load_seed, run_seed


@pytest.fixture
async def engine():
    eng = create_async_engine(get_settings().database_url)
    try:
        async with eng.connect() as conn:
            await conn.execute(text("SELECT 1 FROM locations LIMIT 1"))
    except (OSError, SQLAlchemyError):  # no server, or the tables do not exist yet
        await eng.dispose()
        pytest.skip("database with tables not available")
    yield eng
    await eng.dispose()


async def test_seed_twice_gives_same_counts(engine: AsyncEngine):
    data = load_seed()
    first = await run_seed(engine, data)
    second = await run_seed(engine, data)
    assert first == second
    assert first["locations"] >= len(data["locations"])
    assert first["nav_nodes"] >= len(data["nodes"])


async def test_search_text_is_folded(engine: AsyncEngine):
    await run_seed(engine, load_seed())
    async with engine.connect() as conn:
        row = await conn.execute(
            text("SELECT search_text FROM locations WHERE code = 'D-IBD0'")
        )
        # "İbadethane" is stored as "ibadethane", so typing it without Turkish letters works
        assert "ibadethane" in row.scalar_one()


def test_seed_file_is_valid():
    data = load_seed()  # raises ValueError on a broken file
    assert len(data["locations"]) >= 10
