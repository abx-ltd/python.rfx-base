from rfx_base import config
from alembic_utils.pg_view import PGView

mailbox_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_mailbox",
    definition=f"""
    SELECT
        -- =========================
        -- BASE (ORM REQUIRED)
        -- =========================
        mb._id,
        mb._created,
        mb._updated,
        mb._deleted,

        -- =========================
        -- MAILBOX
        -- =========================
        mb.name AS mailbox_name,
        mb.profile_id AS mailbox_profile_id,
        mb.telecom_phone,
        mb.telecom_email,
        mb.description,
        mb.resource,
        mb.url,
        mb.mailbox_type,

        -- =========================
        -- MESSAGE IDS
        -- =========================
        (
        SELECT COALESCE(
                array_agg(DISTINCT mm.message_id),
                ARRAY[]::uuid[]
            )
            FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox_message mm
            WHERE mm.mailbox_id = mb._id
            AND mm._deleted IS NULL
            AND mm.message_id IS NOT NULL
        ) AS message_id,

        -- =========================
        -- MESSAGES (FULL OBJECT)
        -- =========================
        COALESCE(
            jsonb_agg(
                DISTINCT jsonb_build_object(
                    'mailbox_message_id', mm._id,
                    'source', mm.source,
                    'source_id', mm.source_id,
                    'category_id', mm.category_id,
                    'profile_id', mm.profile_id,
                    'direction', mm.direction,
                    'status', mm.status,
                    'is_archived', mm.is_archived,
                    'is_starred', mm.is_starred,
                    'mm_created', mm._created,
                    'mm_updated', mm._updated,

                    'message_id', m._id,
                    'subject', m.subject,
                    'content', m.content,
                    'rendered_content', m.rendered_content,
                    'content_type', m.content_type,
                    'is_important', m.is_important,
                    'expirable', m.expirable,
                    'expiration_date', m.expiration_date,
                    'request_read_receipt', m.request_read_receipt,
                    'priority', m.priority,
                    'message_type', m.message_type,
                    'delivery_status', m.delivery_status,
                    'data', m.data,
                    'context', m.context,
                    'category', m.category,
                    'template_key', m.template_key,
                    'template_version', m.template_version,
                    'template_locale', m.template_locale,
                    'template_engine', m.template_engine,
                    'template_data', m.template_data,
                    'render_strategy', m.render_strategy,
                    'render_status', m.render_status,
                    'rendered_at', m.rendered_at,
                    'render_error', m.render_error,
                    'message_created_at', m._created,
                    'message_updated_at', m._updated
                )
            ) FILTER (WHERE m._id IS NOT NULL),
            '[]'::jsonb
        ) AS message

    FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox_message mm
        ON mm.mailbox_id = mb._id
        AND mm._deleted IS NULL

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m
        ON m._id = mm.message_id
        AND m._deleted IS NULL

    WHERE mb._deleted IS NULL

    GROUP BY
        mb._id,
        mb._created,
        mb._updated,
        mb._deleted,
        mb.name,
        mb.profile_id,
        mb.telecom_phone,
        mb.telecom_email,
        mb.description,
        mb.resource,
        mb.url,
        mb.mailbox_type
    """,
)