"""
Utility helpers for seeding database tables from CSV snapshots.

Designed to be flexible: provide schema + table + CSV path, and the loader will
truncate the target table (unless disabled) then bulk insert rows.
"""

import csv
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import text

from rfx_base import config
from rfx_user.state import IDMStateManager
from rfx_policy.state import PolicyStateManager

# Accept common timestamp formats seen in seed CSVs (with or without fractional seconds, tz offset optional).
_DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S.%f %z",
    "%Y-%m-%d %H:%M:%S %z",
    "%Y-%m-%d %H:%M:%S.%f%z",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
]

_TZ_SUFFIX_RE = re.compile(r"([+-])(\d{2})(?::?(\d{2}))?$")


def _looks_like_uuid(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        UUID(value)
    except (ValueError, TypeError):
        return False
    else:
        return True


def _normalize_tz_suffix(value: str) -> str:
    match = _TZ_SUFFIX_RE.search(value)
    if not match:
        return value
    minutes = match.group(3) or "00"
    normalized_suffix = f"{match.group(1)}{match.group(2)}:{minutes}"
    return f"{value[: match.start()]}{normalized_suffix}"


def _coerce_value(value: object) -> object:
    """Normalize CSV values for DB insertion."""
    if value is None:
        return None

    if isinstance(value, (list, tuple)):
        # DictReader stores overflow columns under a list; grab the first real value.
        for entry in value:
            if entry not in (None, ""):
                value = entry
                break
        else:
            return None

    if not isinstance(value, str):
        return value

    value = value.strip()
    if value == "" or value.lower() == "null":
        return None

    # Convert common literal bool strings to actual booleans for correct DB binding.
    lower_value = value.lower()
    if lower_value in {"true", "false"}:
        return lower_value == "true"

    # Normalize timezone suffixes so Python's datetime parser accepts strings like "+07".
    normalized_value = _normalize_tz_suffix(value)
    if normalized_value.endswith(("Z", "z")):
        normalized_value = normalized_value[:-1] + "+00:00"

    # Try ISO 8601 first to catch offsets like "+07" that strptime won't parse.
    try:
        return datetime.fromisoformat(normalized_value)
    except ValueError:
        pass

    # Try specific datetime formats so asyncpg binds real datetime objects instead of text.
    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(normalized_value, fmt)
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
                if key is None:
                    # Skip unrecognized columns created by stray delimiters in the CSV file.
                    continue
                cleaned[key] = _coerce_value(value)
            cleaned.setdefault("_realm", None)
            if not cleaned.get("_id") and _looks_like_uuid(cleaned.get("_created")):
                # Repair rows where columns were shifted (e.g., _id empty but _created holds the UUID).
                cleaned["_id"] = cleaned["_created"]
                created_timestamp = cleaned.get("_updated")
                if isinstance(created_timestamp, datetime):
                    cleaned["_created"] = created_timestamp
                else:
                    cleaned["_created"] = datetime.now(UTC)
                cleaned["_updated"] = None
            # Ensure mandatory audit fields are populated when missing in the snapshot.
            if cleaned.get("_created") is None:
                cleaned["_created"] = datetime.now(UTC)
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


async def _get_table_columns(conn, schema: str, table: str) -> list[str]:
    """
    Fetch actual column names for a table so inserts only reference existing columns.
    """
    sql = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table
        ORDER BY ordinal_position
        """
    )
    result = await conn.execute(sql, {"schema": schema, "table": table})
    return [row[0] for row in result]


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

    async with engine.begin() as conn:
        table_columns = await _get_table_columns(conn, schema, table)
        if not table_columns:
            raise ValueError(f"No columns found for {schema}.{table}")
        columns = [col for col in table_columns if col in rows[0]]
        if not columns:
            raise ValueError(
                f"Seed data has no matching columns for {schema}.{table}"
            )
        cleaned_rows = [
            {col: row.get(col) for col in columns}
            for row in rows
        ]
        placeholders = ", ".join(f":{col}" for col in columns)
        column_sql = ", ".join(columns)
        insert_sql = text(
            f"INSERT INTO {schema}.{table} ({column_sql}) VALUES ({placeholders})"
        )
        if truncate:
            await conn.execute(text(f"DELETE FROM {schema}.{table}"))
        await conn.execute(insert_sql, cleaned_rows)


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
