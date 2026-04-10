from rfx_base import config
from alembic_utils.pg_view import PGView

message_mailbox_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_message_mailbox",
    definition=f"""
    SELECT
        -- =========================
        -- MAILBOX
        -- =========================
        mb._id AS mailbox_id,
        mb.name AS mailbox_name,

        -- =========================
        -- USER (CRITICAL)
        -- =========================
        mm.assigned_to_profile_id AS profile_id,

        -- =========================
        -- MESSAGE STATE
        -- =========================
        mm._id AS mailbox_message_id,
        mm.message_id,
        mm.folder,
        mm.is_starred,
        mm.read_at,
        mm.status,
        mm._created AS mm_created,

        -- =========================
        -- MESSAGE
        -- =========================
        m.subject,
        m.content,
        m.rendered_content,
        m.content_type,
        m.is_important,
        m.priority,
        m.message_type,
        m._created AS message_created_at,

        -- =========================
        -- CATEGORY
        -- =========================
        cat._id AS category_id,
        cat.name AS category_name,
        cat.key AS category_key,

        -- =========================
        -- TAGS
        -- =========================
        (
            SELECT COALESCE(
                jsonb_agg(
                    jsonb_build_object(
                        'tag_id', t._id,
                        'tag_name', t.name
                    )
                ), '[]'::jsonb
            )
            FROM {config.RFX_2DMESSAGE_SCHEMA}.message_tag mt
            JOIN {config.RFX_2DMESSAGE_SCHEMA}.tag t ON t._id = mt.tag_id
            WHERE mt.message_id = m._id
            AND mt._deleted IS NULL
            AND t._deleted IS NULL
        ) AS tags,

        -- =========================
        -- ATTACHMENTS
        -- =========================
        (
            SELECT COALESCE(
                jsonb_agg(
                    jsonb_build_object(
                        'attachment_id', ma._id,
                        'file_name', ma.file_name
                    )
                ), '[]'::jsonb
            )
            FROM {config.RFX_2DMESSAGE_SCHEMA}.message_attachment ma
            WHERE ma.message_id = m._id
            AND ma._deleted IS NULL
        ) AS attachments

    FROM {config.RFX_2DMESSAGE_SCHEMA}.message_mailbox_state mm

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb
        ON mb._id = mm.mailbox_id
    AND mb._deleted IS NULL

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m
        ON m._id = mm.message_id
    AND m._deleted IS NULL

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message_category mc
        ON mc.message_id = m._id
    AND mc._deleted IS NULL

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.category cat
        ON cat._id = mc.category_id
    AND cat._deleted IS NULL

    WHERE mm._deleted IS NULL;
    """,
)