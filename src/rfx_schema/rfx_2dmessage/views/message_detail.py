from rfx_base import config
from alembic_utils.pg_view import PGView

message_detail_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_message_detail",
    definition=f"""
    SELECT
        m._id,
        mm._id AS mailbox_message_id,

        mm.mailbox_id,
        mb.name AS mailbox_name,

        mm.message_id,
        mm.assigned_to_profile_id,
        mm.folder,
        mm.status,
        mm.is_starred,

        -- sender (single)
        (
            SELECT s.sender_id
            FROM {config.RFX_2DMESSAGE_SCHEMA}.message_sender s
            WHERE s.message_id = m._id
            AND s._deleted IS NULL
            LIMIT 1
        ) AS sender_id,

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

        -- message
        m.subject,
        m.content,
        m.rendered_content,
        m.content_type,
        m.priority,
        m.message_type,
        m.expirable,
        m.expiration_date,
        m.is_important,

        -- =========================
        -- CATEGORY (FIXED)
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

        -- attachments
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'attachment_id', ma.media_entry_id,

                        -- từ media_entry
                        'file_name', me.filename,

                        -- từ message_attachment
                        'media_type', ma.media_type,
                        'display_order', ma.display_order,
                        'is_primary', ma.is_primary

                        -- optional nếu bạn có
                        -- 'download_policy', me.download_policy
                    )
                    ORDER BY ma.display_order NULLS LAST, me.filename
                )
                FROM {config.RFX_2DMESSAGE_SCHEMA}.message_attachment ma
                JOIN "cpo-media"."media-entry" me
                    ON me._id = ma.media_entry_id
                    AND me._deleted IS NULL
                WHERE ma.message_id = m._id
                AND ma._deleted IS NULL
            ),
            '[]'::jsonb
        ) AS attachments,

        -- LINKED MESSAGES
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'message_id', m2._id,
                        'subject', m2.subject,
                        'content', m2.content,
                        'message_type', m2.message_type,
                        'created_at', m2._created,
                        'link_type', ml.link_type
                    )
                    ORDER BY m2._created DESC
                )
                FROM {config.RFX_2DMESSAGE_SCHEMA}.message_link ml
                JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m2
                    ON m2._id = ml.left_message_id
                AND m2._deleted IS NULL
                WHERE ml.right_message_id = m._id
                AND ml._deleted IS NULL
            ),
            '[]'::jsonb
        ) AS linked_messages,

        -- actions (per mailbox)
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'action_id', act._id,
                        'action_key', act.action_key,
                        'name', act.name,
                        'action_type', act.action_type,
                        'execution_mode', act.execution_mode,
                        'authorization_type', act.authorization_type,
                        'endpoint_json', act.endpoint_json,
                        'embedded_json', act.embedded_json,
                        'schema_json', act.schema_json,
                        'response_json', act.response_json,
                        'enabled', act.enabled
                    )
                )
                FROM {config.RFX_2DMESSAGE_SCHEMA}.message_action act
                WHERE act.mailbox_id = mm.mailbox_id
                AND act._deleted IS NULL
            ),
            '[]'::jsonb
        ) AS actions,

        mm.read_at,
        mm._created AS is_assigned_at,

        mm._created,
        mm._updated,
        mm._deleted,
        mm._realm,
        mm._creator,
        mm._updater,
        mm._etag


    FROM {config.RFX_2DMESSAGE_SCHEMA}.message_mailbox_state mm

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb
        ON mb._id = mm.mailbox_id
    AND mb._deleted IS NULL

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m
        ON m._id = mm.message_id
    AND m._deleted IS NULL

    -- =========================
    -- CATEGORY JOIN (FIXED)
    -- =========================
    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.category cat
        ON cat._id = m.category_id
    AND cat.mailbox_id = mm.mailbox_id
    AND cat._deleted IS NULL

    WHERE mm._deleted IS NULL;
    """
)