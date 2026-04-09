from rfx_base import config
from alembic_utils.pg_view import PGView

message_sender_detail_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_message_sender_detail",
    definition=f"""
    SELECT
        -- Message Sender Information
        ms._id AS _id,
        ms.sender_id,
        ms.direction AS sender_direction,
        
        -- Message Information
        m._id AS message_id,
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
        m._created AS message_created_at,
        m._updated AS message_updated_at,
        m._creator,
        m._updater,
        m._deleted,
        m._etag,
        
        -- Mailbox Message Information
        mm._id AS mailbox_message_id,
        mm.mailbox_id,
        mm.source,
        mm.source_id,
        mm.category_id,
        mm.profile_id AS mailbox_profile_id,
        mm.direction AS mailbox_direction,
        mm.status AS mailbox_status,
        mm.is_archived,
        mm.is_starred,
        mm._created AS mailbox_created_at,
        mm._updated AS mailbox_updated_at,
        
        -- Sender Profile Information
        jsonb_build_object(
            'id', p._id,
            'preferred_name', p.preferred_name,
            'given_name', p.name__given,
            'middle_name', p.name__middle,
            'family_name', p.name__family,
            'prefix', p.name__prefix,
            'suffix', p.name__suffix
        ) AS sender_profile,
        
        -- Mailbox Information (owner)
        jsonb_build_object(
            'id', pmb._id,
            'preferred_name', pmb.preferred_name,
            'given_name', pmb.name__given,
            'middle_name', pmb.name__middle,
            'family_name', pmb.name__family,
            'prefix', pmb.name__prefix,
            'suffix', pmb.name__suffix
        ) AS mailbox_owner
    FROM {config.RFX_2DMESSAGE_SCHEMA}.message_sender ms
    JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m ON m._id = ms.message_id AND m._deleted IS NULL
    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.message_mailbox_state mm ON mm.message_id = m._id AND mm._deleted IS NULL
    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb_temp ON mb_temp._id = mm.mailbox_id AND mb_temp._deleted IS NULL
    LEFT JOIN {config.RFX_USER_SCHEMA}.profile pmb ON pmb._id = mb_temp.profile_id AND pmb._deleted IS NULL
    LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = ms.sender_id AND p._deleted IS NULL
    WHERE ms._deleted IS NULL
    """,
)