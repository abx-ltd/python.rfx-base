# helper.py
from __future__ import annotations

import uuid
from typing import Any

from ._meta import config
from .types import EntryTypeEnum


def split_path(path: str) -> tuple[str, str]:
    if "/" in path:
        return path.rsplit("/", 1)
    return "", path


async def ensure_entry_path_available(
    statemgr: Any,
    *,
    cabinet_id: uuid.UUID,
    path: str,
) -> None:
    """Optimistic check — unique index is the true safety net."""
    if await statemgr.exist("entry", where={"cabinet_id": cabinet_id, "path": path}):
        raise ValueError(f"An entry already exists at path '{path}'")


def apply_move_updates(updates: dict[str, Any], *, new_path: str) -> None:
    new_parent_path, new_name = split_path(new_path)
    updates["parent_path"] = new_parent_path
    updates["name"] = new_name


async def move_folder_descendants(
    statemgr: Any,
    *,
    entry: Any,
    old_path: str,
    new_path: str,
) -> None:
    """
    Bulk-move all descendants in a single atomic UPDATE.
    """
    if entry.type != EntryTypeEnum.FOLDER:
        return

    old_prefix = f"{old_path}/"
    new_prefix = f"{new_path}/"
    # Postgres SUBSTR is 1-based: SUBSTR(col, N+1) skips first N chars.
    old_prefix_len = len(old_prefix)

    await statemgr.native_query(
        f"""
        UPDATE "{config.RFX_DOCMAN_SCHEMA}"."entry"
           SET parent_path = CASE
                 WHEN parent_path = $3 THEN $1
                 ELSE $2 || SUBSTR(parent_path, $4 + 1)
               END
         WHERE cabinet_id = $5
           AND (parent_path = $3 OR parent_path LIKE $6)
           AND _deleted IS NULL
        """,
        new_path,              # $1  direct children
        new_prefix,            # $2  deep descendants prefix
        old_path,              # $3  equality match
        old_prefix_len,        # $4  SUBSTR offset
        entry.cabinet_id,      # $5
        f"{old_prefix}%",      # $6  prefix scan
        unwrapper=None,
    )
