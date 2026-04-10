# helper.py
from __future__ import annotations

from typing import Any

from ._meta import config
from .types import EntryTypeEnum


def split_path(path: str) -> tuple[str, str]:
    if "/" in path:
        return path.rsplit("/", 1)
    return "", path


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
           AND _deleted IS NULL
           AND (
                parent_path = $3
                OR parent_path LIKE $6
           )
        """,
        new_path,  # $1 direct children new parent_path
        new_prefix,  # $2 deep descendants new prefix: "<new_path>/"
        old_path,  # $3 direct-children old parent_path
        old_prefix_len,  # $4 SUBSTR offset
        entry.cabinet_id,  # $5
        f"{old_path}/%",  # $6 old subtree selector for descendants
        unwrapper=None,
    )


async def resolve_parent_entry(
    statemgr: Any,
    *,
    cabinet_id: Any,
    parent_path: str,
) -> Any | None:
    """Resolve and validate parent entry by display path."""
    if not parent_path:
        return None

    parent = await statemgr.exist(
        "entry",
        where={
            "cabinet_id": cabinet_id,
            "path": parent_path,
        },
    )
    if not parent:
        raise ValueError(f"Parent path '{parent_path}' does not exist")
    if parent.type != EntryTypeEnum.FOLDER:
        raise ValueError(f"Parent path '{parent_path}' is not a folder")
    return parent


async def insert_entry_ancestor_rows(
    statemgr: Any,
    *,
    entry_id: Any,
    parent_id: Any | None,
) -> None:
    """Insert closure rows for a newly created entry."""
    await statemgr.native_query(
        f"""
        INSERT INTO "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
            (ancestor_id, descendant_id, depth)
        VALUES ($1, $1, 0)
        ON CONFLICT (ancestor_id, descendant_id) DO UPDATE
            SET depth = EXCLUDED.depth
        """,
        entry_id,
        unwrapper=None,
    )

    if parent_id is None:
        return

    await statemgr.native_query(
        f"""
        INSERT INTO "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
            (ancestor_id, descendant_id, depth)
        SELECT
            ea.ancestor_id,
            $1,
            ea.depth + 1
        FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor" ea
        WHERE ea.descendant_id = $2
        ON CONFLICT (ancestor_id, descendant_id) DO UPDATE
            SET depth = EXCLUDED.depth
        """,
        entry_id,
        parent_id,
        unwrapper=None,
    )


async def rebuild_subtree_ancestors(
    statemgr: Any,
    *,
    entry_id: Any,
    new_parent_id: Any | None,
) -> None:
    """Rebuild closure links from new ancestors to moved subtree.

    When `new_parent_id` is None (move to root), `new_ancestors` is empty.
    This is expected: old external ancestors are removed, while subtree self-links
    remain intact because old_ancestors excludes `ancestor_id = entry_id`.
    """
    if new_parent_id is not None:
        cycle = await statemgr.exist(
            "entry_ancestor",
            where={
                "ancestor_id": entry_id,
                "descendant_id": new_parent_id,
            },
        )
        if cycle:
            raise ValueError("Cannot move a folder into itself or its descendants")

    await statemgr.native_query(
        f"""
        WITH subtree AS (
            SELECT
                descendant_id,
                depth AS depth_from_root
            FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
            WHERE ancestor_id = $1
        ),
        old_ancestors AS (
            SELECT ancestor_id
            FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
            WHERE descendant_id = $1
              AND ancestor_id <> $1
        ),
        deleted AS (
            DELETE FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor" ea
            USING old_ancestors oa, subtree s
            WHERE ea.ancestor_id = oa.ancestor_id
              AND ea.descendant_id = s.descendant_id
        ),
        new_ancestors AS (
            SELECT ancestor_id, depth
            FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
            WHERE descendant_id = $2
        )
        INSERT INTO "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
            (ancestor_id, descendant_id, depth)
        SELECT
            na.ancestor_id,
            s.descendant_id,
            na.depth + 1 + s.depth_from_root
        FROM new_ancestors na
        CROSS JOIN subtree s
        ON CONFLICT (ancestor_id, descendant_id) DO UPDATE
            SET depth = EXCLUDED.depth
        """,
        entry_id,
        new_parent_id,
        unwrapper=None,
    )
