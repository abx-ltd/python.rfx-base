from rfx_base import config
from alembic_utils.pg_view import PGView

message_tag_view= PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_message_tag",
    definition=f"""
    SELECT
        -- =========================
        -- MESSAGE_TAG RELATION
        -- =========================
        t._id,
        mt._id AS message_tag_id,
        mt.message_id,
        mt.tag_id,

        -- =========================
        -- MAILBOX
        -- =========================
        mb._id AS mailbox_id,
        mb.name AS mailbox_name,

        -- =========================
        -- ASSIGNMENT
        -- =========================
        mm.assigned_to_profile_id,

        -- =========================
        -- MESSAGE STATE
        -- =========================
        mm._id AS mailbox_message_state_id,
        mm.folder,
        mm.is_starred,
        mm.read_at,
        mm.status,
        mm._created AS is_assigned_at,

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
        -- CATEGORY (1-1)
        -- =========================
        m.category_id,
        cat.name AS category_name,
        cat.key AS category_key,

        -- =========================
        -- TAG (CURRENT ROW)
        -- =========================
        t.key AS tag_key,
        t.name AS tag_name,

        -- =========================
        -- ATTACHMENTS (same as mailbox view)
        -- =========================
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'attachment_id', ma._id,
                        'file_name', ma.file_name
                    )
                    ORDER BY ma._created
                )
                FROM {config.RFX_2DMESSAGE_SCHEMA}.message_attachment ma
                WHERE ma.message_id = m._id
                AND ma._deleted IS NULL
            ),
            '[]'::jsonb
        ) AS attachments,

        -- =========================
        -- MAILBOX METADATA
        -- =========================
        t._created,
        t._updated,
        t._deleted,
        t._realm,
        t._creator,
        t._updater,
        t._etag

    FROM {config.RFX_2DMESSAGE_SCHEMA}.message_tag mt

    -- =========================
    -- MESSAGE
    -- =========================
    JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m
        ON m._id = mt.message_id
    AND m._deleted IS NULL

    -- =========================
    -- MAILBOX STATE (CRITICAL JOIN)
    -- =========================
    JOIN {config.RFX_2DMESSAGE_SCHEMA}.message_mailbox_state mm
        ON mm.message_id = m._id
    AND mm._deleted IS NULL

    -- =========================
    -- MAILBOX
    -- =========================
    JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb
        ON mb._id = mm.mailbox_id
    AND mb._deleted IS NULL

    -- =========================
    -- CATEGORY
    -- =========================
    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.category cat
        ON cat._id = m.category_id
    AND cat.mailbox_id = mm.mailbox_id
    AND cat._deleted IS NULL

    -- =========================
    -- TAG (SCOPED TO MAILBOX)
    -- =========================
    JOIN {config.RFX_2DMESSAGE_SCHEMA}.tag t
        ON t._id = mt.tag_id
    AND t.mailbox_id = mm.mailbox_id
    AND t._deleted IS NULL

    WHERE mt._deleted IS NULL;
    """
)