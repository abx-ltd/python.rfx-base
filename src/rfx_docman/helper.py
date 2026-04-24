"""Helper functions for docman path and closure-table operations."""

from __future__ import annotations

from typing import Any, Callable

from asyncpg import UniqueViolationError
from fluvius.data.exceptions import DuplicateEntryError, ItemNotFoundError
from fluvius.error import BadRequestError

from ._meta import config
from .types import EntryTypeEnum


async def ensure_parent_hierarchy(
    statemgr: Any,
    *,
    cabinet_id: Any,
    parent_path: str,
    init_resource: Callable[..., Any],
    id_generator: Callable[[], Any],
) -> Any | None:
    """Ensure full folder hierarchy exists for parent_path and return last parent."""
    if not parent_path:
        return None

    parent = None
    current_parent_path = ""

    for segment in parent_path.split("/"):
        current_path = (
            segment if not current_parent_path else f"{current_parent_path}/{segment}"
        )
        existing = await statemgr.exist(
            "entry",
            where={"cabinet_id": cabinet_id, "path": current_path},
        )
        if existing:
            if existing.type != EntryTypeEnum.FOLDER:
                raise BadRequestError(
                    "D10.001",
                    f"Parent path '{current_path}' exists but is not a folder",
                )
            parent = existing
            current_parent_path = current_path
            continue

        folder = init_resource(
            "entry",
            {
                "cabinet_id": cabinet_id,
                "parent_path": current_parent_path,
                "name": segment,
                "type": EntryTypeEnum.FOLDER,
                "media_entry_id": None,
                "is_virtual": True,
            },
            _id=id_generator(),
        )
        try:
            await statemgr.insert(folder)
            await insert_entry_ancestor_rows(
                statemgr,
                entry_id=folder._id,
                parent_id=parent._id if parent else None,
            )
            parent = folder
        except UniqueViolationError:
            # Concurrent create of same folder path: re-fetch and continue.
            existing = await statemgr.exist(
                "entry",
                where={"cabinet_id": cabinet_id, "path": current_path},
            )
            if not existing:
                raise
            if existing.type != EntryTypeEnum.FOLDER:
                raise BadRequestError(
                    "D10.001",
                    f"Parent path '{current_path}' exists but is not a folder",
                )
            parent = existing

        current_parent_path = current_path

    return parent


def split_path(path: str) -> tuple[str, str]:
    """Split absolute entry path into `(parent_path, name)`."""
    if "/" in path:
        return path.rsplit("/", 1)
    return "", path


def apply_move_updates(updates: dict[str, Any], *, new_path: str) -> None:
    """Normalize update payload fields from a resolved absolute path."""
    new_parent_path, new_name = split_path(new_path)
    updates["parent_path"] = new_parent_path
    updates["name"] = new_name


async def move_folder_descendants(
    statemgr: Any,
    *,
    entry: Any,
    old_path: str,
    new_path: str,
    source_cabinet_id: Any,
    dest_cabinet_id: Any,
) -> None:
    """Bulk-move descendants of a folder in one SQL update statement."""
    if entry.type != EntryTypeEnum.FOLDER:
        return

    # Stage 1: derive old/new subtree prefixes for path rewrites.
    old_prefix = f"{old_path}/"
    new_prefix = f"{new_path}/"
    # Postgres SUBSTR is 1-based: SUBSTR(col, N+1) skips first N chars.
    old_prefix_len = len(old_prefix)

    # Stage 2: rewrite descendant parent_path and optionally cabinet_id.
    await statemgr.native_query(
        f"""
        UPDATE "{config.RFX_DOCMAN_SCHEMA}"."entry"
           SET parent_path = CASE
                 WHEN parent_path = $3 THEN $1
                 ELSE $2 || SUBSTR(parent_path, $4 + 1)
               END,
               cabinet_id = $7
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
        source_cabinet_id,  # $5
        f"{old_path}/%",  # $6 old subtree selector for descendants
        dest_cabinet_id,  # $7
        unwrapper=None,
    )


async def fetch_entry_subtree(
    statemgr: Any,
    *,
    ancestor_id: Any,
) -> tuple[list[dict], dict]:
    """Fetch subtree rows ordered by depth and build a path-to-id index.

    Returns:
        (rows, path_to_old_id) where:
          - rows        : list of plain dicts with keys (_id, parent_path, name,
                          type, media_entry_id, is_virtual, depth, _path).
                          ``_path`` is the pre-computed ``parent_path/name`` value.
          - path_to_old_id : mapping of each entry's ``_path`` → its ``_id``,
                          used for O(1) parent-ID resolution without extra queries.

    Note:
        ``native_query`` returns ``SimpleNamespace`` objects (via list_unwrapper);
        this helper converts them to plain dicts before returning.
    """
    # Stage 1: fetch ancestor closure rows joined with live entries.
    ns_rows = await statemgr.native_query(
        f"""
        SELECT
            e._id,
            e.parent_path,
            e.name,
            e.type,
            e.media_entry_id,
            e.is_virtual,
            ea.depth
        FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor" ea
        JOIN "{config.RFX_DOCMAN_SCHEMA}"."entry" e
            ON e._id = ea.descendant_id
        WHERE ea.ancestor_id = $1
          AND e._deleted IS NULL
        ORDER BY ea.depth ASC
        """,
        ancestor_id,
    )

    result: list[dict] = []
    path_to_old_id: dict = {}

    # Stage 2: normalize rows to dict + pre-computed `_path` index.
    for ns in ns_rows:
        # native_query returns SimpleNamespace; convert to plain dict first.
        row = vars(ns)
        path = (
            f"{row['parent_path']}/{row['name']}" if row["parent_path"] else row["name"]
        )
        row["_path"] = path
        result.append(row)
        path_to_old_id[path] = row["_id"]

    return result, path_to_old_id


async def insert_entry_ancestor_rows(
    statemgr: Any,
    *,
    entry_id: Any,
    parent_id: Any | None,
) -> None:
    """Insert closure rows for a new node (`self` + inherited ancestors)."""
    # Stage 1: always ensure self-link (depth=0).
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

    # Stage 2: inherit all ancestors from parent with depth + 1.
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
    """Rebuild external closure links after moving an entry subtree.

    When `new_parent_id` is None (move to root), `new_ancestors` is empty.
    This is expected: old external ancestors are removed, while subtree self-links
    remain intact because old_ancestors excludes `ancestor_id = entry_id`.
    """
    # Stage 1: cycle guard for folder moves.
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

    # Stage 2: replace only external ancestor edges for the moved subtree.
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


async def prune_entry_ancestor_for_soft_delete(
    statemgr: Any,
    *,
    entry_id: Any,
) -> None:
    """Remove closure rows tied to a soft-deleted entry.

    Soft-delete keeps rows in `entry`, so FK `ON DELETE CASCADE` on
    `entry_ancestor` is not triggered. Pruning these closure rows keeps the
    closure table compact while preserving live-entry ancestry.
    """
    # Stage 1: remove every edge where this node is ancestor or descendant.
    await statemgr.native_query(
        f"""
        DELETE FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
         WHERE ancestor_id = $1
            OR descendant_id = $1
        """,
        entry_id,
        unwrapper=None,
    )


async def cascade_soft_delete_subtree(
    statemgr: Any,
    *,
    root_id: Any,
) -> None:
    """Cascade soft-delete all live descendants of a folder and prune the entire subtree's closure rows.

    The root entry itself must be invalidated separately via ``statemgr.invalidate()``
    before calling this function to ensure proper ``_etag`` / ``_updater`` bookkeeping.

    Algorithm (3 SQL statements regardless of subtree depth):
    1. Collect all subtree IDs (root + descendants) from the closure table.
    2. Bulk soft-delete every live descendant (root excluded — already invalidated).
    3. Prune ALL closure edges where any subtree member is ancestor or descendant.
    """
    # Stage 1: collect every ID in the subtree via the closure self-link (depth >= 0).
    subtree_rows = await statemgr.native_query(
        f"""
        SELECT descendant_id AS entry_id
        FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
        WHERE ancestor_id = $1
        """,
        root_id,
    )
    # Fall back to [root_id] if closure is missing the self-link (data corruption guard).
    subtree_ids = [row.entry_id for row in subtree_rows] if subtree_rows else [root_id]

    # Stage 2: bulk soft-delete all live descendants; skip root (already invalidated).
    await statemgr.native_query(
        f"""
        UPDATE "{config.RFX_DOCMAN_SCHEMA}"."entry"
           SET _deleted = NOW()
         WHERE _id = ANY($1)
           AND _id <> $2
           AND _deleted IS NULL
        """,
        subtree_ids,
        root_id,
        unwrapper=None,
    )

    # Stage 3: remove all closure edges for the entire subtree in one pass.
    await statemgr.native_query(
        f"""
        DELETE FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
         WHERE ancestor_id = ANY($1)
            OR descendant_id = ANY($1)
        """,
        subtree_ids,
        unwrapper=None,
    )


async def delete_entry_tag_link(
    statemgr: Any,
    *,
    entry_id: Any,
    tag_id: Any,
) -> None:
    """Hard-delete an entry-tag junction row.

    `entry_tag` is a technical junction table (composite PK, no `_id/_etag`),
    so it must be removed with SQL delete instead of `invalidate`.
    """
    await statemgr.native_query(
        f"""
        DELETE FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_tag"
         WHERE entry_id = $1
           AND tag_id = $2
        """,
        entry_id,
        tag_id,
        unwrapper=None,
    )


async def _fetch_deleted_entry_root(
    statemgr: Any,
    *,
    entry_id: Any,
) -> Any:
    rows = await statemgr.native_query(
        f"""
        SELECT _id, cabinet_id, parent_path, path, type
        FROM "{config.RFX_DOCMAN_SCHEMA}"."entry"
        WHERE _id = $1
          AND _deleted IS NOT NULL
        LIMIT 1
        """,
        entry_id,
    )
    if not rows:
        raise ItemNotFoundError("E00.006", f"Deleted entry '{entry_id}' not found")
    return rows[0]


async def _fetch_deleted_subtree_rows(
    statemgr: Any,
    *,
    cabinet_id: Any,
    root_path: str,
) -> list[Any]:
    path_prefix = f"{root_path}/%"
    return await statemgr.native_query(
        f"""
        SELECT _id, cabinet_id, parent_path, path
        FROM "{config.RFX_DOCMAN_SCHEMA}"."entry"
        WHERE cabinet_id = $1
          AND _deleted IS NOT NULL
          AND (path = $2 OR path LIKE $3)
        ORDER BY LENGTH(path) ASC, path ASC
        """,
        cabinet_id,
        root_path,
        path_prefix,
    )


async def restore_deleted_entry_subtree(
    statemgr: Any,
    *,
    entry_id: Any,
) -> int:
    """Restore a deleted entry (and subtree for folders) using SQL/native_query."""
    root = await _fetch_deleted_entry_root(statemgr, entry_id=entry_id)
    deleted_rows = await _fetch_deleted_subtree_rows(
        statemgr,
        cabinet_id=root.cabinet_id,
        root_path=str(root.path),
    )
    if not deleted_rows:
        raise ItemNotFoundError("E00.006", f"Deleted entry '{entry_id}' not found")

    # Include deleted ancestor chain so restoring a node can also recover
    # required parent folders when they are in bin.
    rows_by_path: dict[str, Any] = {str(row.path): row for row in deleted_rows}
    parent_path = str(root.parent_path or "")
    while parent_path:
        if parent_path in rows_by_path:
            break

        deleted_parent_rows = await statemgr.native_query(
            f"""
            SELECT _id, cabinet_id, parent_path, path, type
            FROM "{config.RFX_DOCMAN_SCHEMA}"."entry"
            WHERE cabinet_id = $1
              AND path = $2
              AND _deleted IS NOT NULL
            ORDER BY _deleted DESC
            LIMIT 1
            """,
            root.cabinet_id,
            parent_path,
        )
        if deleted_parent_rows:
            deleted_parent = deleted_parent_rows[0]
            parent_type = getattr(deleted_parent.type, "value", deleted_parent.type)
            if str(parent_type) != EntryTypeEnum.FOLDER.value:
                raise BadRequestError(
                    "D10.004",
                    f"Cannot restore because parent '{parent_path}' is not a folder",
                )
            rows_by_path[parent_path] = deleted_parent
            parent_path = str(deleted_parent.parent_path or "")
            continue

        active_parent_rows = await statemgr.native_query(
            f"""
            SELECT _id
            FROM "{config.RFX_DOCMAN_SCHEMA}"."entry"
            WHERE cabinet_id = $1
              AND path = $2
              AND _deleted IS NULL
            LIMIT 1
            """,
            root.cabinet_id,
            parent_path,
        )
        if active_parent_rows:
            break

        raise BadRequestError(
            "D10.004",
            f"Cannot restore '{root.path}' because parent '{parent_path}' is missing",
        )

    rows_to_restore = sorted(
        rows_by_path.values(),
        key=lambda row: (len(str(row.path)), str(row.path)),
    )
    restore_ids = [row._id for row in rows_to_restore]
    restore_paths = [str(row.path) for row in rows_to_restore]

    # Guard: any active path collision blocks restore.
    conflicts = await statemgr.native_query(
        f"""
        SELECT path
        FROM "{config.RFX_DOCMAN_SCHEMA}"."entry"
        WHERE cabinet_id = $1
          AND _deleted IS NULL
          AND path = ANY($2)
        LIMIT 1
        """,
        root.cabinet_id,
        restore_paths,
    )
    if conflicts:
        raise DuplicateEntryError(
            "E00.001",
            f"Cannot restore because path '{conflicts[0].path}' already exists",
        )

    try:
        await statemgr.native_query(
            f"""
            UPDATE "{config.RFX_DOCMAN_SCHEMA}"."entry"
               SET _deleted = NULL
             WHERE _id = ANY($1)
               AND _deleted IS NOT NULL
            """,
            restore_ids,
            unwrapper=None,
        )
    except UniqueViolationError:
        # Concurrent create/restore can race with the pre-check above.
        conflicts = await statemgr.native_query(
            f"""
            SELECT path
            FROM "{config.RFX_DOCMAN_SCHEMA}"."entry"
            WHERE cabinet_id = $1
              AND _deleted IS NULL
              AND path = ANY($2)
            LIMIT 1
            """,
            root.cabinet_id,
            restore_paths,
        )
        conflict_path = conflicts[0].path if conflicts else "<unknown>"
        raise DuplicateEntryError(
            "E00.001",
            f"Cannot restore because path '{conflict_path}' already exists",
        )

    # Rebuild closure rows from active parent chain (restored + existing).
    await statemgr.native_query(
        f"""
        DELETE FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
         WHERE ancestor_id = ANY($1)
            OR descendant_id = ANY($1)
        """,
        restore_ids,
        unwrapper=None,
    )

    restored_rows = await statemgr.native_query(
        f"""
        SELECT _id, cabinet_id, parent_path, path
        FROM "{config.RFX_DOCMAN_SCHEMA}"."entry"
        WHERE _id = ANY($1)
          AND _deleted IS NULL
        ORDER BY LENGTH(path) ASC, path ASC
        """,
        restore_ids,
    )

    restored_path_to_id: dict[str, Any] = {
        str(row.path): row._id for row in restored_rows
    }

    for row in restored_rows:
        parent_id = None
        parent_path = str(row.parent_path or "")
        if parent_path:
            # Fast path: parent is in the same restored subtree.
            parent_id = restored_path_to_id.get(parent_path)
            if parent_id is None:
                parent_rows = await statemgr.native_query(
                    f"""
                    SELECT _id
                    FROM "{config.RFX_DOCMAN_SCHEMA}"."entry"
                    WHERE cabinet_id = $1
                      AND path = $2
                      AND _deleted IS NULL
                    LIMIT 1
                    """,
                    row.cabinet_id,
                    parent_path,
                )
                if not parent_rows:
                    raise BadRequestError(
                        "D10.004",
                        f"Cannot restore '{row.path}' because parent '{parent_path}' is missing",
                    )
                parent_id = parent_rows[0]._id

        await insert_entry_ancestor_rows(
            statemgr,
            entry_id=row._id,
            parent_id=parent_id,
        )

    return len(restore_ids)


async def hard_delete_deleted_entry_subtree(
    statemgr: Any,
    *,
    entry_id: Any,
) -> int:
    """Hard-delete a deleted entry (and subtree) with direct SQL bypass."""
    root = await _fetch_deleted_entry_root(statemgr, entry_id=entry_id)
    deleted_rows = await _fetch_deleted_subtree_rows(
        statemgr,
        cabinet_id=root.cabinet_id,
        root_path=str(root.path),
    )
    if not deleted_rows:
        raise ItemNotFoundError("E00.006", f"Deleted entry '{entry_id}' not found")

    delete_ids = [row._id for row in deleted_rows]

    await statemgr.native_query(
        f"""
        DELETE FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_tag"
         WHERE entry_id = ANY($1)
        """,
        delete_ids,
        unwrapper=None,
    )

    await statemgr.native_query(
        f"""
        DELETE FROM "{config.RFX_DOCMAN_SCHEMA}"."entry_ancestor"
         WHERE ancestor_id = ANY($1)
            OR descendant_id = ANY($1)
        """,
        delete_ids,
        unwrapper=None,
    )

    await statemgr.native_query(
        f"""
        DELETE FROM "{config.RFX_DOCMAN_SCHEMA}"."entry"
         WHERE _id = ANY($1)
           AND _deleted IS NOT NULL
        """,
        delete_ids,
        unwrapper=None,
    )
    return len(delete_ids)
