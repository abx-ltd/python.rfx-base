from rfx_base import config
from alembic_utils.pg_view import PGView

message_outbox_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_outbox",
    definition=f"""
WITH thread_agg AS (
    SELECT
        m.thread_id,
        MIN(m._created) AS first_created_at,
        COUNT(*) AS message_count
    FROM {config.RFX_MESSAGE_SCHEMA}.message m
    WHERE m._deleted IS NULL
    GROUP BY m.thread_id
),
first_message AS (
    SELECT DISTINCT ON (m.thread_id)
        m.sender_id,
        m.thread_id,
        m.subject,
        m.content,
        m.rendered_content,
        m.content_type,
        m.tags,
        m.is_important,
        m.expirable,
        m.expiration_date,
        m.request_read_receipt,
        m.priority,
        m.message_type,
        m.delivery_status,
        m.data,
        m.context,
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
        m._id,
        m._created,
        m._updated,
        m._creator,
        m._updater,
        m._deleted,
        m._etag,
        (ma._id IS NOT NULL) AS archived,
        (mt._id IS NOT NULL) AS trashed,
        mc.category
    FROM {config.RFX_MESSAGE_SCHEMA}.message m
    LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_category mc
        ON mc.resource = 'message'
       AND mc.resource_id = m._id
       AND mc._deleted IS NULL
    LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_archived ma
        ON ma.resource = 'message'
       AND ma.resource_id = m._id
       AND ma._deleted IS NULL
    LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_trashed mt
        ON mt.resource = 'message'
       AND mt.resource_id = m._id
       AND mt._deleted IS NULL
    WHERE m._deleted IS NULL
    ORDER BY m.thread_id, m._created
)

SELECT
    m._id,
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
    ARRAY_AGG(DISTINCT r.recipient_id)
        FILTER (WHERE r.recipient_id IS NOT NULL) AS recipient_id,
    jsonb_agg(
        DISTINCT jsonb_build_object(
            'id', rp._id,
            'preferred_name', rp.preferred_name,
            'given_name', rp.name__given,
            'middle_name', rp.name__middle,
            'family_name', rp.name__family,
            'prefix', rp.name__prefix,
            'suffix', rp.name__suffix
        )
    ) FILTER (WHERE rp._id IS NOT NULL) AS recipient_profile,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    BOOL_OR(r.read)          AS is_read,
    MAX(r.mark_as_read)     AS recipient_read_at,
    BOOL_OR(m.archived)     AS archived,
    BOOL_OR(m.trashed)     AS trashed,
    mc.category,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag,
    ta.message_count
FROM first_message m
JOIN thread_agg ta
    ON ta.thread_id = m.thread_id
JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON m._id = r.message_id
LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_category mc
    ON mc.resource = 'message'
   AND mc.resource_id = m._id
   AND mc._deleted IS NULL
LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = m.sender_id
   AND sp._deleted IS NULL
LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id
   AND rp._deleted IS NULL
GROUP BY
    m._id,
    m.thread_id,
    m.sender_id,
    sp._id, sp.preferred_name, sp.name__given,
    sp.name__middle, sp.name__family,
    sp.name__prefix, sp.name__suffix,
    m.subject,
    m.content,
    m.content_type,
    m.tags,
    m.expirable,
    m.priority,
    m.message_type,
    mc.category,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag,
    ta.message_count
ORDER BY m._created DESC;
    """,
)
