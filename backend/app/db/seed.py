"""Put campus data from a JSON file into the database (A-08).

Idempotent: running it twice gives the same rows, because every write is
"insert, or update if it already exists".

Run it with the command line tool:  python tools/build_seed.py
"""

import json
from pathlib import Path
from typing import Any

from geoalchemy2 import WKTElement
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.text import fold_tr
from app.db.models import (
    AccessPoint,
    AdminUser,
    Base,
    Building,
    Floor,
    Location,
    NavEdge,
    NavNode,
    Person,
)

# repo root = backend/app/db/seed.py -> three levels up
DEFAULT_SEED_FILE = Path(__file__).resolve().parents[3] / "data" / "seed" / "fake_d_block.json"


def load_seed(path: Path = DEFAULT_SEED_FILE) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    validate_seed(data)
    return data


def validate_seed(data: dict[str, Any]) -> None:
    """Catch typos in the data file before touching the database."""
    levels = {f["level"] for f in data["floors"]}
    refs = [n["ref"] for n in data["nodes"]]
    if len(refs) != len(set(refs)):
        raise ValueError("node ref codes must be unique inside one building")
    for n in data["nodes"]:
        if n["level"] not in levels:
            raise ValueError(f"node {n['ref']}: unknown floor level {n['level']}")
    for e in data["edges"]:
        for end in (e["a"], e["b"]):
            if end not in refs:
                raise ValueError(f"edge {e['a']} -> {e['b']}: unknown node {end}")
    codes = [loc["code"] for loc in data["locations"]]
    if len(codes) != len(set(codes)):
        raise ValueError("location codes must be unique")
    for loc in data["locations"]:
        if loc["level"] not in levels:
            raise ValueError(f"location {loc['code']}: unknown floor level {loc['level']}")
        if loc.get("door") and loc["door"] not in refs:
            raise ValueError(f"location {loc['code']}: unknown door node {loc['door']}")


def _point(x: float, y: float) -> WKTElement:
    return WKTElement(f"POINT({x} {y})", srid=0)


async def _upsert(session: AsyncSession, model: Any, values: dict[str, Any], keys: list[Any]) -> int:
    """INSERT ... ON CONFLICT (keys) DO UPDATE ... RETURNING id."""
    insert_stmt = pg_insert(model).values(**values)
    key_names = {k.key for k in keys}
    changes = {name: insert_stmt.excluded[name] for name in values if name not in key_names}
    upsert = insert_stmt.on_conflict_do_update(index_elements=keys, set_=changes)
    return int((await session.execute(upsert.returning(model.id))).scalar_one())


async def seed(session: AsyncSession, data: dict[str, Any]) -> None:
    b = data["building"]
    building_id = await _upsert(session, Building, b, [Building.code])

    floor_ids: dict[int, int] = {}
    for f in data["floors"]:
        values = {**f, "building_id": building_id}
        floor_ids[f["level"]] = await _upsert(session, Floor, values, [Floor.building_id, Floor.level])

    # Nodes and edges have no unique column in the table, so we look them up first.
    node_ids: dict[str, int] = {}
    for n in data["nodes"]:
        values = {
            "floor_id": floor_ids[n["level"]],
            "kind": n["kind"],
            "geom": _point(n["x"], n["y"]),
            "is_accessible": n["accessible"],
            "ref_code": n["ref"],
        }
        found = await session.scalar(
            select(NavNode.id)
            .join(Floor, NavNode.floor_id == Floor.id)
            .where(Floor.building_id == building_id, NavNode.ref_code == n["ref"])
        )
        if found is None:
            node_ids[n["ref"]] = int(
                (await session.execute(pg_insert(NavNode).values(**values).returning(NavNode.id)))
                .scalar_one()
            )
        else:
            await session.execute(update(NavNode).where(NavNode.id == found).values(**values))
            node_ids[n["ref"]] = found

    for e in data["edges"]:
        values = {
            "from_node": node_ids[e["a"]],
            "to_node": node_ids[e["b"]],
            "weight_m": e["weight_m"],
            "kind": e["kind"],
            "is_accessible": e["accessible"],
            "floors_spanned": e["floors_spanned"],
        }
        found = await session.scalar(
            select(NavEdge.id).where(
                NavEdge.from_node == values["from_node"], NavEdge.to_node == values["to_node"]
            )
        )
        if found is None:
            await session.execute(pg_insert(NavEdge).values(**values))
        else:
            await session.execute(update(NavEdge).where(NavEdge.id == found).values(**values))

    for loc in data["locations"]:
        values = {
            "floor_id": floor_ids[loc["level"]],
            "code": loc["code"],
            "name": loc["name"],
            "name_tr": loc.get("name_tr"),
            "type": loc["type"],
            "subtype": loc.get("subtype"),
            "geom": _point(loc["x"], loc["y"]),
            "door_node_id": node_ids.get(loc.get("door", "")),
            "is_accessible": loc["accessible"],
            # The same function that will fold the user's search text (A-05).
            "search_text": fold_tr(f"{loc['code']} {loc['name']} {loc.get('name_tr') or ''}"),
        }
        await _upsert(session, Location, values, [Location.code])


COUNTED = [Building, Floor, NavNode, NavEdge, Location, Person, AccessPoint, AdminUser]


async def count_rows(session: AsyncSession) -> dict[str, int]:
    counts: dict[str, int] = {}
    for model in COUNTED:
        table = Base.metadata.tables[model.__tablename__]
        counts[table.name] = int(await session.scalar(select(func.count()).select_from(table)) or 0)
    return counts


async def run_seed(engine: AsyncEngine, data: dict[str, Any]) -> dict[str, int]:
    """Seed in one transaction (all or nothing), then return the row counts."""
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        async with session.begin():
            await seed(session, data)
        return await count_rows(session)
