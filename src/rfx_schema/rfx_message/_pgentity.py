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
        m.sender_id,
        r.recipient_id,
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
        ON m._id = r.message_id;
    """,
)

message_outbox_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_outbox",
    definition=f"""
    SELECT
        m._id,
        m.sender_id,
        ARRAY_AGG(DISTINCT r.recipient_id)
            FILTER (WHERE r.recipient_id IS NOT NULL) AS recipient_id,
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
        m._etag
    FROM {config.RFX_MESSAGE_SCHEMA}.message m
    JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
        ON m._id = r.message_id
    GROUP BY
        m._id,
        m.sender_id,
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
        m._etag;
    """,
)

message_box_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_box",
    definition=f"""
SELECT
    r._id,
    m.sender_id,
 	ARRAY[r.recipient_id]::uuid[] AS recipient_id,
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
    NULL::uuid           AS target_profile_id,
    'INBOX'              AS box_type
FROM {config.RFX_MESSAGE_SCHEMA}.message m
JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON m._id = r.message_id

UNION ALL

SELECT
    m._id,
    m.sender_id,
    ARRAY_AGG(DISTINCT r.recipient_id)
        FILTER (WHERE r.recipient_id IS NOT NULL)
        ::uuid[]              AS recipient_id,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    BOOL_OR(r.read) AS is_read,
    MAX(r.mark_as_read)     AS recipient_read_at,
    m.archived,
    m.trashed,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag,
    m.sender_id::uuid       AS target_profile_id,
    'OUTBOX'                AS box_type
FROM {config.RFX_MESSAGE_SCHEMA}.message m
JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
     ON m._id = r.message_id
GROUP BY
    m._id,
    m.sender_id,
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
    m._etag;
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
        ]
    )


register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
