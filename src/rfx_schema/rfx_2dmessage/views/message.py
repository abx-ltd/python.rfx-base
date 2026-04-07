from rfx_base import config
from alembic_utils.pg_view import PGView

message_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_message",
    definition=f"""
    SELECT
        m._id AS _id,
        m.subject,
        m.content,
        m.rendered_content,
        m.content_type,
        m.is_important,
        m.expirable,
        m.expiration_date,
        m.request_read_receipt,
        m.priority,
        m.message_type,
        m.delivery_status,
        m.data,
        m.context,
        m.category,
        m.template_key,
        m.template_version,
        m.template_locale,
        m.template_engine,
        m.template_data,
        m.render_strategy,
        m.render_status,
        m.rendered_at,
        m.render_error,
        m._realm,
        m._created,
        m._updated,
        m._creator,
        m._updater,
        m._deleted,
        m._etag,
        COUNT(DISTINCT s._id) AS sender_count,
        COUNT(DISTINCT r._id) AS recipient_count,
        COUNT(DISTINCT a._id) AS attachment_count,
        COUNT(DISTINCT ma._id) FILTER (WHERE ma._deleted IS NULL) AS mailbox_count
    FROM {config.RFX_2DMESSAGE_SCHEMA}.message m
    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message_sender s ON s.message_id = m._id AND s._deleted IS NULL
    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message_recipient r ON r.message_id = m._id AND r._deleted IS NULL
    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message_attachment a ON a.message_id = m._id AND a._deleted IS NULL
    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox_message ma ON ma.message_id = m._id
    WHERE m._deleted IS NULL
    GROUP BY
        m._id, m.subject, m.content, m.rendered_content, m.content_type,
        m.is_important, m.expirable, m.expiration_date, m.request_read_receipt, m.priority,
        m.message_type, m.delivery_status, m.data, m.context, m.category, m.template_key,
        m.template_version, m.template_locale, m.template_engine, m.template_data,
        m.render_strategy, m.render_status, m.rendered_at, m.render_error,
        m._realm, m._created, m._updated, m._creator, m._updater, m._deleted, m._etag
    """,
)
