from alembic_utils.pg_view import PGView
from rfx_base import config

message_inbox_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_inbox",
    definition=f"""
SELECT
    r._id,
    m._id AS message_id,
    m.thread_id,
    m.sender_id,
    jsonb_build_object(
        'id', sp._id,
        'preferred_name', sp.preferred_name,
        'given_name', sp.name__given,
        'middle_name', sp.name__middle,
        'family_name', sp.name__family,
        'prefix', sp.name__prefix,
        'suffix', sp.name__suffix
    ) AS sender_profile,
    r.recipient_id,
    jsonb_build_object(
        'id', rp._id,
        'preferred_name', rp.preferred_name,
        'given_name', rp.name__given,
        'middle_name', rp.name__middle,
        'family_name', rp.name__family,
        'prefix', rp.name__prefix,
        'suffix', rp.name__suffix
    ) AS recipient_profile,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    mc.category,
    r.read               AS is_read,
    r.mark_as_read       AS recipient_read_at,
    (ma._id IS NOT NULL) AS archived,
    (mt._id IS NOT NULL) AS trashed,
    r._realm,
    r._created,
    r._updated,
    r._creator,
    r._updater,
    r._deleted,
    r._etag
FROM {config.RFX_MESSAGE_SCHEMA}.message m
JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON m._id = r.message_id
LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_category mc
    ON mc.resource = 'message_recipient'
   AND mc.resource_id = r._id
   AND mc._deleted IS NULL
LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_archived ma
    ON ma.resource = 'message_recipient'
   AND ma.resource_id = r._id
   AND ma._deleted IS NULL
LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_trashed mt
    ON mt.resource = 'message_recipient'
   AND mt.resource_id = r._id
   AND mt._deleted IS NULL
LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = m.sender_id
   AND sp._deleted IS NULL
LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id
   AND rp._deleted IS NULL;
    """,
)
