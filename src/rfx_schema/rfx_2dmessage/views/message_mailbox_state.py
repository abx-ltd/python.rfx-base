from rfx_base import config
from alembic_utils.pg_view import PGView

message_mailbox_state_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_message_mailbox_state",
    definition=f"""
SELECT
    mm._id AS mailbox_message_id,
    mm._created AS mailbox_state_created_at,
    mm._updated AS mailbox_state_updated_at,
    mm._deleted,
    mm.mailbox_id,
    mb.name AS mailbox_name,
    mm.message_id,
    mm.assigned_to_profile_id,
    mm.folder,
    mm.read,
    mm.read_at,
    mm.status,
    mm.is_starred,
    (SELECT s.sender_id
       FROM {config.RFX_2DMESSAGE_SCHEMA}.message_sender s
      WHERE s.message_id = m._id
        AND s._deleted IS NULL
      LIMIT 1
    ) AS sender_id,
    ARRAY( 
        SELECT DISTINCT r._id
          FROM {config.RFX_2DMESSAGE_SCHEMA}.message_recipient r
         WHERE r.message_id = m._id
           AND r._deleted IS NULL
    ) AS recipient_ids,
    m.subject,
    m.content,
    m.rendered_content,
    m.content_type,
    m.priority,
    m.message_type,
    m.expirable,
    m.expiration_date,
    m.request_read_receipt,
    mc.category_id,
    cat.name AS category_name,
    cat.key AS category_key,
    COALESCE(
        (SELECT jsonb_agg(jsonb_build_object(
            'tag_id', t._id,
            'tag_key', t.key,
            'tag_name', t.name,
            'background_color', t.background_color,
            'font_color', t.font_color,
            'description', t.description
        ))
         FROM {config.RFX_2DMESSAGE_SCHEMA}.message_tag mt
         JOIN {config.RFX_2DMESSAGE_SCHEMA}.tag t ON t._id = mt.tag_id AND t._deleted IS NULL
         WHERE mt.message_id = m._id
           AND mt._deleted IS NULL
        ), '[]'::jsonb
    ) AS tags,
    ARRAY(
        SELECT DISTINCT t.key
          FROM {config.RFX_2DMESSAGE_SCHEMA}.message_tag mt
          JOIN {config.RFX_2DMESSAGE_SCHEMA}.tag t ON t._id = mt.tag_id AND t._deleted IS NULL
         WHERE mt.message_id = m._id
           AND mt._deleted IS NULL
    ) AS tag_keys,
    COALESCE(
        (SELECT jsonb_agg(jsonb_build_object(
            'attachment_id', ma._id,
            'file_id', ma.file_id,
            'file_name', ma.file_name,
            'storage_key', ma.storage_key,
            'media_type', ma.media_type,
            'size_bytes', ma.size_bytes,
            'checksum', ma.checksum,
            'download_policy', ma.download_policy
        ))
         FROM {config.RFX_2DMESSAGE_SCHEMA}.message_attachment ma
         WHERE ma.message_id = m._id
           AND ma._deleted IS NULL
        ), '[]'::jsonb
    ) AS attachments,
    COALESCE(
        (SELECT jsonb_agg(jsonb_build_object(
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
        ))
         FROM {config.RFX_2DMESSAGE_SCHEMA}.message_action act
         WHERE act.mailbox_id = mm.mailbox_id
           AND act._deleted IS NULL
        ), '[]'::jsonb
    ) AS actions
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
WHERE mm._deleted IS NULL
""",
)
