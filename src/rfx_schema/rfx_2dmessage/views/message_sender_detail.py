from rfx_base import config
from alembic_utils.pg_view import PGView

message_sender_detail_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_message_sender_detail",
    definition=f"""
    SELECT
        ms.sender_id,
        m._id AS message_id,
        m.subject,
        m.content,
        ms.box_id,
        ms.direction,
        ms.is_archived,
        ms.is_starred,
        m.thread_id,
        m.content_type,
        m.priority,
        m.message_type,
        m.category,
        m._created AS message_created_at,
        m._updated AS message_updated_at,
        mb.key AS box_key,
        mb.name AS box_name,
        mb.type AS box_type_enum,
        jsonb_build_object(
            'id', p._id,
            'preferred_name', p.preferred_name,
            'given_name', p.name__given,
            'middle_name', p.name__middle,
            'family_name', p.name__family,
            'prefix', p.name__prefix,
            'suffix', p.name__suffix
        ) AS sender_profile
    FROM {config.RFX_2DMESSAGE_SCHEMA}.message_sender ms
    JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m ON m._id = ms.message_id
    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message_box mb ON mb._id = ms.box_id AND mb._deleted IS NULL
    LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = ms.sender_id AND p._deleted IS NULL
    WHERE ms._deleted IS NULL
    """,
)