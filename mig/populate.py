"""
Utility helpers for seeding database tables from CSV snapshots.

Designed to be flexible: provide schema + table + CSV path, and the loader will
truncate the target table (unless disabled) then bulk insert rows.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from sqlalchemy import text

from rfx_base import config
from rfx_user.state import IDMStateManager
from rfx_policy.state import PolicyStateManager

# Accept common timestamp formats seen in seed CSVs (with or without fractional seconds, tz offset optional).
_DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S.%f %z",
    "%Y-%m-%d %H:%M:%S %z",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
]


def _coerce_value(value: str) -> object:
    if value == "":
        return None

    # Convert common literal bool strings to actual booleans for correct DB binding.
    lower_value = value.lower()
    if lower_value in {"true", "false"}:
        return lower_value == "true"

    # Try to parse datetime strings so asyncpg binds real datetime objects instead of text.
    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return value


def _read_csv_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = []
        for row in reader:
            cleaned: dict[str, object] = {}
            for key, value in row.items():
                cleaned[key] = _coerce_value(value)
            cleaned.setdefault("_realm", None)
            # Ensure mandatory audit fields are populated when missing in the snapshot.
            if cleaned.get("_created") is None:
                cleaned["_created"] = datetime.utcnow()
            rows.append(cleaned)
    return rows


def _get_engine_for_schema(schema: str):
    """
    Return an async engine using the domain-specific state manager for a schema.
    """
    if schema == config.RFX_POLICY_SCHEMA:
        manager = PolicyStateManager(None)
    elif schema == config.RFX_USER_SCHEMA:
        manager = IDMStateManager(None)
    else:
        raise ValueError(f"No state manager configured for schema '{schema}'")

    return manager.connector._session_configuration._async_engine


async def import_csv(
    schema: str,
    table: str,
    csv_path: Path,
    *,
    engine=None,
    truncate: bool = True,
):
    """
    Import a CSV file into a specific table, optionally truncating first.
    """
    if engine is None:
        engine = _get_engine_for_schema(schema)

    if not csv_path.exists():
        raise FileNotFoundError(f"Seed file not found: {csv_path}")

    rows = _read_csv_rows(csv_path)
    if not rows:
        return

    columns = list(rows[0].keys())
    placeholders = ", ".join(f":{col}" for col in columns)
    column_sql = ", ".join(columns)
    insert_sql = text(
        f"INSERT INTO {schema}.{table} ({column_sql}) VALUES ({placeholders})"
    )

    async with engine.begin() as conn:
        if truncate:
            await conn.execute(text(f"DELETE FROM {schema}.{table}"))
        await conn.execute(insert_sql, rows)


async def seed_policy_data():
    """
    Seed policy tables from CSV snapshots under mig/policy.
    """
    base_path = Path(__file__).resolve().parent / "policy"
    engine = _get_engine_for_schema(config.RFX_POLICY_SCHEMA)
    tables: Sequence[tuple[str, Path]] = [
        ("policy", base_path / "policy.csv"),
        ("policy_resource", base_path / "policy_resource.csv"),
        ("policy_role", base_path / "policy_role.csv"),
    ]

    # Truncate in dependency order (role first to drop FKs, then resource, then policy)
    async with engine.begin() as conn:
        await conn.execute(text(f"DELETE FROM {config.RFX_POLICY_SCHEMA}.policy_role"))
        await conn.execute(text(f"DELETE FROM {config.RFX_POLICY_SCHEMA}.policy_resource"))
        await conn.execute(text(f"DELETE FROM {config.RFX_POLICY_SCHEMA}.policy"))

    for table, csv_path in tables:
        await import_csv(config.RFX_POLICY_SCHEMA, table, csv_path, engine=engine, truncate=False)


async def seed_system_roles(csv_path: Optional[Path] = None):
    """
    Seed ref__system_role in the user schema. If no path is provided, use the
    default snapshot path under mig/ref_system_role.
    """
    if csv_path is None:
        csv_path = Path(__file__).resolve().parent / "ref_system_role" / "ref__system_role.csv"

    await import_csv(
        config.RFX_USER_SCHEMA,
        "ref__system_role",
        csv_path,
        engine=_get_engine_for_schema(config.RFX_USER_SCHEMA),
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_policy_data())
    asyncio.run(seed_system_roles())
