import os
from rfx_schema import logger
from rfx_base import config
from rfx_schema.rfx_media import SCHEMA as MEDIA_SCHEMA

from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities

realm_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_realm",
    definition=f"""
    SELECT
        r.*,
        COALESCE(m.meta, '{{}}'::json) AS realm_meta,
        COALESCE(s.shelf_count, 0) AS shelf_count
    FROM "{config.RFX_DOCMAN_SCHEMA}".realm r
    LEFT JOIN (
        SELECT realm_id,
            json_object_agg(key, value) AS meta
        FROM "{config.RFX_DOCMAN_SCHEMA}".realm_meta
        WHERE _deleted IS NULL
        AND key = ANY (
            ARRAY['REALM','SHELF','CATEGORY','CABINET']::"{config.RFX_DOCMAN_SCHEMA}".realmmetakeyenum[]
        )
        GROUP BY realm_id
    ) m ON m.realm_id = r._id
    LEFT JOIN (
        SELECT realm_id,
            COUNT(*)::int AS shelf_count
        FROM "{config.RFX_DOCMAN_SCHEMA}".shelf
        WHERE _deleted IS NULL
        GROUP BY realm_id
    ) s ON s.realm_id = r._id
    WHERE r._deleted IS NULL;
    """,
)

shelf_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_shelf",
    definition=f"""
    SELECT
        s.*,
        COALESCE(c.category_count, 0) AS category_count
    FROM "{config.RFX_DOCMAN_SCHEMA}".shelf s
    LEFT JOIN (
        SELECT
            c.shelf_id,
            COUNT(*)::int AS category_count
        FROM "{config.RFX_DOCMAN_SCHEMA}".category c
        WHERE c._deleted IS NULL
        GROUP BY c.shelf_id
    ) c ON c.shelf_id = s._id
    WHERE s._deleted IS NULL;
    """,
)

category_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_category",
    definition=f"""
    SELECT
        c.*,
        COALESCE(cb.cabinet_count, 0) AS cabinet_count
    FROM "{config.RFX_DOCMAN_SCHEMA}".category c
    LEFT JOIN (
        SELECT
            cb.category_id,
            COUNT(*)::int AS cabinet_count
        FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
        WHERE cb._deleted IS NULL
        GROUP BY cb.category_id
    ) cb ON cb.category_id = c._id
    WHERE c._deleted IS NULL;
    """,
)

cabinet_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_cabinet",
    definition=f"""
    SELECT
        cb.*,
        COALESCE(e.entry_count, 0) AS entry_count
    FROM "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
    LEFT JOIN (
        SELECT
            e.cabinet_id,
            COUNT(*)::int AS entry_count
        FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
        WHERE e._deleted IS NULL
        GROUP BY e.cabinet_id
    ) e ON e.cabinet_id = cb._id
    WHERE cb._deleted IS NULL;
    """,
)

entry_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_entry",
    definition=f"""
    WITH RECURSIVE
    real_entries AS (
        SELECT
            e._created,
            e._creator,
            e._etag,
            e._id,
            e._updated,
            e._updater,
            e._deleted,
            e._realm,
            cb.realm_id AS realm_id,
            e.cabinet_id,
            e.parent_path,
            e.path,
            e.name,
            e.type,
            e.status,
            e.media_entry_id,
            me.filename,
            me.filehash,
            me.filemime,
            me.length,
            me.resource,
            me.resource__id,
            COALESCE(tag_agg.tags, '[]'::json) AS tags,
            FALSE AS is_virtual
        FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
        JOIN "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
          ON cb._id = e.cabinet_id
         AND cb._deleted IS NULL
        LEFT JOIN "{MEDIA_SCHEMA}"."media-entry" me
          ON me._id = e.media_entry_id
        LEFT JOIN LATERAL (
            SELECT json_agg(t.name ORDER BY t.name) AS tags
            FROM "{config.RFX_DOCMAN_SCHEMA}".entry_tag et
            JOIN "{config.RFX_DOCMAN_SCHEMA}".tag t
              ON t._id = et.tag_id
             AND t._deleted IS NULL
            WHERE et.entry_id = e._id
              AND et._deleted IS NULL
        ) tag_agg ON TRUE
        WHERE e._deleted IS NULL
    ),
    entry_paths AS (
        SELECT DISTINCT
            e.cabinet_id,
            e.path
        FROM "{config.RFX_DOCMAN_SCHEMA}".entry e
        WHERE e._deleted IS NULL
          AND e.path IS NOT NULL
          AND position('/' in e.path) > 0
    ),
    path_parts AS (
        SELECT
            ep.cabinet_id,
            string_to_array(ep.path, '/') AS parts
        FROM entry_paths ep
    ),
    virtual_builder AS (
        SELECT
            pp.cabinet_id,
            pp.parts[1] AS name,
            ''::text AS parent_path,
            pp.parts[1] AS path,
            2 AS depth,
            array_length(pp.parts, 1) AS total_depth,
            pp.parts
        FROM path_parts pp
        WHERE array_length(pp.parts, 1) >= 2

        UNION ALL

        SELECT
            vb.cabinet_id,
            vb.parts[vb.depth] AS name,
            vb.path AS parent_path,
            vb.path || '/' || vb.parts[vb.depth] AS path,
            vb.depth + 1 AS depth,
            vb.total_depth,
            vb.parts
        FROM virtual_builder vb
        WHERE vb.depth < vb.total_depth
    ),
    virtual_folders AS (
        SELECT DISTINCT
            vb.cabinet_id,
            vb.path,
            vb.name,
            vb.parent_path
        FROM virtual_builder vb
        LEFT JOIN "{config.RFX_DOCMAN_SCHEMA}".entry e
          ON e.cabinet_id = vb.cabinet_id
         AND e.path = vb.path
         AND e._deleted IS NULL
        WHERE e._id IS NULL
    ),
    virtual_entries AS (
        SELECT
            NOW() AS _created,
            NULL::uuid AS _creator,
            NULL::text AS _etag,
            uuid_generate_v5(uuid_ns_url(), vf.cabinet_id::text || ':' || vf.path) AS _id,
            NOW() AS _updated,
            NULL::uuid AS _updater,
            NULL::timestamp with time zone AS _deleted,
            cb._realm,
            cb.realm_id,
            vf.cabinet_id,
            vf.parent_path,
            vf.path,
            vf.name,
            'FOLDER'::"{config.RFX_DOCMAN_SCHEMA}".entrytypeenum AS type,
            NULL::"{config.RFX_DOCMAN_SCHEMA}".entrystatusenum AS status,
            NULL::uuid AS media_entry_id,
            NULL::text AS filename,
            NULL::text AS filehash,
            NULL::text AS filemime,
            NULL::bigint AS length,
            NULL::text AS resource,
            NULL::uuid AS resource__id,
            '[]'::json AS tags,
            TRUE AS is_virtual
        FROM virtual_folders vf
        JOIN "{config.RFX_DOCMAN_SCHEMA}".cabinet cb
          ON cb._id = vf.cabinet_id
         AND cb._deleted IS NULL
    )
    SELECT * FROM real_entries
    UNION ALL
    SELECT * FROM virtual_entries;
    """,
)

tag_view = PGView(
    schema=config.RFX_DOCMAN_SCHEMA,
    signature="_tag",
    definition=f"""
    SELECT
        t._created,
        t._creator,
        t._deleted,
        t._etag,
        t._id,
        t._updated,
        t._updater,
        t._realm,
        t.realm_id,
        tc.cabinet_id,
        t.name,
        t.color,
        t.icon,
        COALESCE(tc.cabinet_ids, '[]'::json) AS cabinet_ids
    FROM "{config.RFX_DOCMAN_SCHEMA}".tag t
    LEFT JOIN (
        SELECT
            et.tag_id,
            MIN(e.cabinet_id::text)::uuid cabinet_id,
            json_agg(DISTINCT e.cabinet_id) AS cabinet_ids
        FROM "{config.RFX_DOCMAN_SCHEMA}".entry_tag et
        JOIN "{config.RFX_DOCMAN_SCHEMA}".entry e
          ON e._id = et.entry_id
         AND e._deleted IS NULL
        WHERE et._deleted IS NULL
        GROUP BY et.tag_id
    ) tc ON tc.tag_id = t._id
    WHERE t._deleted IS NULL;
    """,
)


def register_pg_entities(allow):
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info("REGISTER_PG_ENTITIES for rfx_docman is disabled or not set.")
        return
    register_entities(
        [
            realm_view,
            shelf_view,
            category_view,
            cabinet_view,
            entry_view,
            tag_view,
        ]
    )


register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
