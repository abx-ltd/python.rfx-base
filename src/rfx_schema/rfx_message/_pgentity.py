import os
from rfx_schema import logger
from rfx_base import config

from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities


message_recipient_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_recipient",
    definition=f"""
    SELECT
        message._id,
        r.recipient_id,
        message.subject,
        message.content,
        message.content_type,
        message.sender_id,
        message.tags,
        message.expirable,
        message.priority,
        message.message_type,
        message.category,
        r.read              AS is_read,
        r.mark_as_read      AS read_at,
        r._id               AS record_id,
        r.archived,
        r.trashed,
        message._realm,
        message._created,
        message._updated,
        message._creator,
        message._updater,
        message._deleted,
        message._etag
    FROM {config.RFX_MESSAGE_SCHEMA}.message
    JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
         ON message._id = r.message_id;
    """,
)


def register_pg_entities(allow):
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info("REGISTER_PG_ENTITIES is disabled or not set.")
        return
    register_entities(
        [
            message_recipient_view,
        ]
    )


register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
