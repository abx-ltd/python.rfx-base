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
        m._id,
        mb._id AS mailbox_id,
        mb.name AS mailbox_name,

        -- =========================
        -- ASSIGNMENT
        -- =========================
        mm.assigned_to_profile_id,

        -- =========================
        -- SENDER
        -- =========================

        (
            SELECT p.name__given
            FROM {config.RFX_2DMESSAGE_SCHEMA}.message_sender s
            JOIN {config.RFX_USER_SCHEMA}.profile p
                ON p._id = s.sender_id
                AND p._deleted IS NULL
            WHERE s.message_id = m._id
                AND s._deleted IS NULL
            LIMIT 1
        ) AS sender_name,

        (
            SELECT p.telecom__email
            FROM {config.RFX_2DMESSAGE_SCHEMA}.message_sender s
            JOIN {config.RFX_USER_SCHEMA}.profile p
                ON p._id = s.sender_id
                AND p._deleted IS NULL
            WHERE s.message_id = m._id
                AND s._deleted IS NULL
            LIMIT 1
        ) AS sender_email,

        -- =========================
        -- MESSAGE STATE
        -- =========================
        mm._id AS mailbox_message_state_id,
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
        -- CATEGORY (1-1)
        -- =========================
        m.category_id,
        cat.name AS category_name,
        cat.key AS category_key,

        -- =========================
        -- TAGS (N-N, mailbox scoped)
        -- =========================
        COALESCE(
            (
                SELECT jsonb_agg(jsonb_build_object(
                    'tag_id', t._id,
                    'key', t.key,
                    'name', t.name
                ) ORDER BY t.name)
                FROM {config.RFX_2DMESSAGE_SCHEMA}.message_tag mt
                JOIN {config.RFX_2DMESSAGE_SCHEMA}.tag t 
                    ON t._id = mt.tag_id
                AND t.mailbox_id = mm.mailbox_id
                AND t._deleted IS NULL
                WHERE mt.message_id = m._id
                AND mt._deleted IS NULL
            ),
            '[]'::jsonb
        ) AS tags,

        -- =========================
        -- ATTACHMENTS (FIXED)
        -- =========================
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'attachment_id', ma.media_entry_id,
                        'file_name', me.filename,
                        'media_type', ma.media_type,
                        'display_order', ma.display_order,
                        'is_primary', ma.is_primary
                    )
                    ORDER BY ma.display_order NULLS LAST
                )
                FROM {config.RFX_2DMESSAGE_SCHEMA}.message_attachment ma
                JOIN "cpo-media"."media-entry" me
                    ON me._id = ma.media_entry_id
                WHERE ma.message_id = m._id
            ),
            '[]'::jsonb
        ) AS attachments,

        m._created,
        m._updated,
        m._deleted,
        m._realm,
        m._creator,
        m._updater,
        m._etag

    FROM {config.RFX_2DMESSAGE_SCHEMA}.message_mailbox_state mm

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb
        ON mb._id = mm.mailbox_id
    AND mb._deleted IS NULL

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m
        ON m._id = mm.message_id
    AND m._deleted IS NULL

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.category cat
        ON cat._id = m.category_id
    AND cat.mailbox_id = mm.mailbox_id
    AND cat._deleted IS NULL

    WHERE mm._deleted IS NULL;
    """
)