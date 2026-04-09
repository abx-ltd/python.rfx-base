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
            FROM {config.RFX_2DMESSAGE_SCHEMA}.message_mailbox_state mm
            WHERE mm.mailbox_id = mb._id
            AND mm._deleted IS NULL
            AND mm.message_id IS NOT NULL
        ) AS message_id,

        -- =========================
        -- MAILBOX MEMBERS
        -- =========================
        (
            SELECT COALESCE(
                jsonb_agg(
                    jsonb_build_object(
                        'member_id', mmbr.member_id,
                        'role', mmbr.role
                    )
                ),
                '[]'::jsonb
            )
            FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox_member mmbr
            WHERE mmbr.mailbox_id = mb._id
            AND mmbr._deleted IS NULL
        ) AS members,

        -- =========================
        -- MESSAGES (FULL OBJECT WITH TAGS, CATEGORY, ATTACHMENTS)
        -- =========================
        COALESCE(
            jsonb_agg(
                DISTINCT jsonb_build_object(
                    'mailbox_message_id', mm._id,
                    'folder', mm.folder,
                    'is_starred', mm.is_starred,
                    'read_at', mm.read_at,
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
                    'message_updated_at', m._updated,

                    'category_name', cat.name,
                    'category_key', cat.key,

                    'tags', (
                        SELECT COALESCE(
                            jsonb_agg(
                                jsonb_build_object(
                                    'tag_id', t2._id,
                                    'tag_key', t2.key,
                                    'tag_name', t2.name,
                                    'background_color', t2.background_color,
                                    'font_color', t2.font_color,
                                    'description', t2.description
                                )
                            ),
                            '[]'::jsonb
                        )
                        FROM {config.RFX_2DMESSAGE_SCHEMA}.message_tag mt2
                        JOIN {config.RFX_2DMESSAGE_SCHEMA}.tag t2 ON t2._id = mt2.tag_id AND t2._deleted IS NULL
                        WHERE mt2.message_id = m._id AND mt2._deleted IS NULL
                    ),

                    'attachments', (
                        SELECT COALESCE(
                            jsonb_agg(
                                jsonb_build_object(
                                    'attachment_id', ma2._id,
                                    'file_id', ma2.file_id,
                                    'file_name', ma2.file_name,
                                    'storage_key', ma2.storage_key,
                                    'media_type', ma2.media_type,
                                    'size_bytes', ma2.size_bytes,
                                    'checksum', ma2.checksum,
                                    'download_policy', ma2.download_policy
                                )
                            ),
                            '[]'::jsonb
                        )
                        FROM {config.RFX_2DMESSAGE_SCHEMA}.message_attachment ma2
                        WHERE ma2.message_id = m._id AND ma2._deleted IS NULL
                    )
                )
            ) FILTER (WHERE m._id IS NOT NULL),
            '[]'::jsonb
        ) AS message

    FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message_mailbox_state mm
        ON mm.mailbox_id = mb._id
        AND mm._deleted IS NULL

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m
        ON m._id = mm.message_id
        AND m._deleted IS NULL

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message_category mc
        ON mc.message_id = m._id
        AND mc._deleted IS NULL

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.category cat
        ON cat._id = mc.category_id
        AND cat._deleted IS NULL

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