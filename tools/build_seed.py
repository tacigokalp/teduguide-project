"""Fill the database with the (fake) campus data.

Run from the backend folder with the virtual environment on:
    python ../tools/build_seed.py
You can run it as many times as you like: the row counts stay the same.
Another data file:  python ../tools/build_seed.py --file path/to/file.json
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Python only looks next to this script (tools/), so tell it where `app` lives.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.seed import DEFAULT_SEED_FILE, load_seed, run_seed


async def main(path: Path) -> None:
    data = load_seed(path)
    engine = create_async_engine(get_settings().database_url)
    try:
        counts = await run_seed(engine, data)
    finally:
        await engine.dispose()
    print(f"Seeded from {path.name}. Row counts now:")
    for table, n in counts.items():
        print(f"  {table:<16} {n}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_SEED_FILE)
    asyncio.run(main(parser.parse_args().file))
