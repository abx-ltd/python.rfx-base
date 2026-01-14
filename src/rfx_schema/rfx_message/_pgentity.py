import os
from rfx_schema import logger
from rfx_base import config

from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities


message_inbox_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_inbox",
    definition=f"""
SELECT
    r._id,
    m._id AS message_id,
    m.thread_id,
    m.sender_id,
    jsonb_build_object(
        'id', sp._id,
        'preferred_name', sp.preferred_name,
        'given_name', sp.name__given,
        'middle_name', sp.name__middle,
        'family_name', sp.name__family,
        'prefix', sp.name__prefix,
        'suffix', sp.name__suffix
    ) AS sender_profile,
    r.recipient_id,
    jsonb_build_object(
        'id', rp._id,
        'preferred_name', rp.preferred_name,
        'given_name', rp.name__given,
        'middle_name', rp.name__middle,
        'family_name', rp.name__family,
        'prefix', rp.name__prefix,
        'suffix', rp.name__suffix
    ) AS recipient_profile,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    r.read               AS is_read,
    r.mark_as_read       AS recipient_read_at,
    r.archived,
    r.trashed,
    r._realm,
    r._created,
    r._updated,
    r._creator,
    r._updater,
    r._deleted,
    r._etag
FROM {config.RFX_MESSAGE_SCHEMA}.message m
JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON m._id = r.message_id
LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = m.sender_id
   AND sp._deleted IS NULL
LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id
   AND rp._deleted IS NULL;
    """,
)

message_outbox_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_outbox",
    definition=f"""
WITH thread_agg AS (
    SELECT
        m.thread_id,
        MIN(m._created) AS first_created_at,
        COUNT(*) AS message_count
    FROM {config.RFX_MESSAGE_SCHEMA}.message m
    WHERE m._deleted IS NULL
    GROUP BY m.thread_id
),
first_message AS (
    SELECT DISTINCT ON (m.thread_id)
        m.*
    FROM {config.RFX_MESSAGE_SCHEMA}.message m
    WHERE m._deleted IS NULL
    ORDER BY m.thread_id, m._created ASC
)
SELECT
    m._id,
    m.thread_id,
    m.sender_id,
    jsonb_build_object(
        'id', sp._id,
        'preferred_name', sp.preferred_name,
        'given_name', sp.name__given,
        'middle_name', sp.name__middle,
        'family_name', sp.name__family,
        'prefix', sp.name__prefix,
        'suffix', sp.name__suffix
    ) AS sender_profile,
    ARRAY_AGG(DISTINCT r.recipient_id) FILTER (WHERE r.recipient_id IS NOT NULL) AS recipient_id,
    jsonb_agg(
        DISTINCT jsonb_build_object(
            'id', rp._id,
            'preferred_name', rp.preferred_name,
            'given_name', rp.name__given,
            'middle_name', rp.name__middle,
            'family_name', rp.name__family,
            'prefix', rp.name__prefix,
            'suffix', rp.name__suffix
        )
    ) FILTER (WHERE rp._id IS NOT NULL) AS recipient_profile,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    BOOL_OR(r.read)      AS is_read,
    MAX(r.mark_as_read) AS recipient_read_at,
    m.archived,
    m.trashed,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag,
    ta.message_count
FROM first_message m
JOIN thread_agg ta
    ON ta.thread_id = m.thread_id
JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON m._id = r.message_id
LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = m.sender_id
   AND sp._deleted IS NULL
LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id
   AND rp._deleted IS NULL
GROUP BY
    m._id,
    m.thread_id,
    m.sender_id,
    sp._id,
    sp.preferred_name,
    sp.name__given,
    sp.name__middle,
    sp.name__family,
    sp.name__prefix,
    sp.name__suffix,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    m.archived,
    m.trashed,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag,
    ta.message_count
ORDER BY m._created DESC;
    """,
)

message_box_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_box",
    definition=f"""
WITH thread_agg AS (
    SELECT
        m.thread_id,
        COUNT(*) AS message_count
    FROM {config.RFX_MESSAGE_SCHEMA}.message m
    WHERE m._deleted IS NULL
    GROUP BY m.thread_id
),
first_message AS (
    SELECT DISTINCT ON (m.thread_id)
        m.*
    FROM {config.RFX_MESSAGE_SCHEMA}.message m
    WHERE m._deleted IS NULL
    ORDER BY m.thread_id, m._created ASC
)

-- ================= INBOX =================
SELECT
    r._id,
    m._id AS message_id,
    m.thread_id,
    m.sender_id,
    jsonb_build_object(
        'id', sp._id,
        'preferred_name', sp.preferred_name,
        'given_name', sp.name__given,
        'middle_name', sp.name__middle,
        'family_name', sp.name__family,
        'prefix', sp.name__prefix,
        'suffix', sp.name__suffix
    ) AS sender_profile,
    ARRAY[r.recipient_id]::uuid[] AS recipient_id,
    jsonb_build_object(
        'id', rp._id,
        'preferred_name', rp.preferred_name,
        'given_name', rp.name__given,
        'middle_name', rp.name__middle,
        'family_name', rp.name__family,
        'prefix', rp.name__prefix,
        'suffix', rp.name__suffix
    ) AS recipient_profile,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    r.read               AS is_read,
    r.mark_as_read       AS recipient_read_at,
    r.archived,
    r.trashed,
    r._realm,
    r._created,
    r._updated,
    r._creator,
    r._updater,
    r._deleted,
    r._etag,
    r.recipient_id::uuid AS target_profile_id,
    NULL::bigint         AS message_count,
    'INBOX'              AS box_type
FROM {config.RFX_MESSAGE_SCHEMA}.message m
JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON m._id = r.message_id
LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = m.sender_id AND sp._deleted IS NULL
LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id AND rp._deleted IS NULL

UNION ALL

-- ================= OUTBOX =================
SELECT
    m._id,
    m._id AS message_id,
    m.thread_id,
    m.sender_id,
    jsonb_build_object(
        'id', sp._id,
        'preferred_name', sp.preferred_name,
        'given_name', sp.name__given,
        'middle_name', sp.name__middle,
        'family_name', sp.name__family,
        'prefix', sp.name__prefix,
        'suffix', sp.name__suffix
    ) AS sender_profile,
    ARRAY_AGG(DISTINCT r.recipient_id) FILTER (WHERE r.recipient_id IS NOT NULL) AS recipient_id,
    jsonb_agg(
        DISTINCT jsonb_build_object(
            'id', rp._id,
            'preferred_name', rp.preferred_name,
            'given_name', rp.name__given,
            'middle_name', rp.name__middle,
            'family_name', rp.name__family,
            'prefix', rp.name__prefix,
            'suffix', rp.name__suffix
        )
    ) FILTER (WHERE rp._id IS NOT NULL) AS recipient_profile,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    BOOL_OR(r.read)          AS is_read,
    MAX(r.mark_as_read)      AS recipient_read_at,
    m.archived,
    m.trashed,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag,
    m.sender_id::uuid        AS target_profile_id,
    ta.message_count         AS message_count,
    'OUTBOX'                 AS box_type
FROM first_message m
JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON m._id = r.message_id
JOIN thread_agg ta
    ON ta.thread_id = m.thread_id
LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = m.sender_id AND sp._deleted IS NULL
LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id AND rp._deleted IS NULL
GROUP BY
    m._id,
    m.thread_id,
    m.sender_id,
    sp._id, sp.preferred_name, sp.name__given,
    sp.name__middle, sp.name__family,
    sp.name__prefix, sp.name__suffix,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    m.archived,
    m.trashed,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag,
    ta.message_count;
    """,
)

message_thread_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_thread",
    definition=f"""
WITH thread_agg AS (
    SELECT
        m.thread_id,
        COUNT(*) AS message_count
    FROM {config.RFX_MESSAGE_SCHEMA}.message m
    WHERE m._deleted IS NULL
    GROUP BY m.thread_id
)
SELECT
    m._id,
    m.thread_id,
    m.sender_id,
    jsonb_build_object(
        'id', sp._id,
        'preferred_name', sp.preferred_name,
        'given_name', sp.name__given,
        'middle_name', sp.name__middle,
        'family_name', sp.name__family,
        'prefix', sp.name__prefix,
        'suffix', sp.name__suffix
    ) AS sender_profile,
    ARRAY_AGG(r.recipient_id ORDER BY r.recipient_id) FILTER (WHERE r.recipient_id IS NOT NULL) ::uuid[] AS recipient_id,
    jsonb_agg(
        DISTINCT jsonb_build_object(
            'id', rp._id,
            'preferred_name', rp.preferred_name,
            'given_name', rp.name__given,
            'middle_name', rp.name__middle,
            'family_name', rp.name__family,
            'prefix', rp.name__prefix,
            'suffix', rp.name__suffix
        )
    ) FILTER (WHERE rp._id IS NOT NULL) AS recipient_profile,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    BOOL_OR(r.read)      AS is_read,
    MAX(r.mark_as_read) AS recipient_read_at,
    m.archived,
    m.trashed,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag,

    ta.message_count

FROM {config.RFX_MESSAGE_SCHEMA}.message m
JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON m._id = r.message_id
JOIN thread_agg ta
    ON ta.thread_id = m.thread_id

LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = m.sender_id AND sp._deleted IS NULL
LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id AND rp._deleted IS NULL

WHERE m._deleted IS NULL

GROUP BY
    m._id,
    m.thread_id,
    m.sender_id,
    sp._id, sp.preferred_name, sp.name__given,
    sp.name__middle, sp.name__family,
    sp.name__prefix, sp.name__suffix,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    m.archived,
    m.trashed,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag,
    ta.message_count

ORDER BY m._created DESC;
    """,
)


def register_pg_entities(allow):
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info("REGISTER_PG_ENTITIES is disabled or not set.")
        return
    register_entities(
        [
            message_inbox_view,
            message_outbox_view,
            message_box_view,
            message_thread_view,
        ]
    )


register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
