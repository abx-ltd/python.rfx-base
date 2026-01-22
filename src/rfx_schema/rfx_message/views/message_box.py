from rfx_base import config
from alembic_utils.pg_view import PGView

message_box_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_box",
    definition=f"""
WITH thread_agg AS (
    SELECT
        m.thread_id,
        COUNT(*) AS message_count
    FROM {config.RFX_MESSAGE_SCHEMA}.message m
    WHERE m._deleted IS NULL
    GROUP BY m.thread_id
),

base AS (

-- ======================================================
-- ROOT: MESSAGE_RECIPIENT
-- ======================================================
SELECT
    r._id,
    m._id AS message_id,
    m.thread_id,
    s.sender_id,

    jsonb_build_object(
        'id', sp._id,
        'preferred_name', sp.preferred_name,
        'given_name', sp.name__given,
        'middle_name', sp.name__middle,
        'family_name', sp.name__family,
        'prefix', sp.name__prefix,
        'suffix', sp.name__suffix
    ) AS sender_profile,

    ARRAY[r.recipient_id] AS recipient_id,

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
    m.expirable,
    m.priority,
    m.message_type,

    m.category,

    r.read         AS is_read,
    r.mark_as_read AS recipient_read_at,

    mb.key  AS box_key,
    mb.name AS box_name,
    mb.type AS box_type_enum,

    r._realm,
    r._created,
    r._updated,
    r._creator,
    r._updater,
    r._deleted,
    r._etag,

    r.recipient_id AS target_profile_id,
    ta.message_count,
    'RECIPIENT'::text AS root_type,
    r.direction,
	ARRAY_REMOVE(ARRAY[mt.key], NULL) AS tags


FROM {config.RFX_MESSAGE_SCHEMA}.message_recipient r
JOIN {config.RFX_MESSAGE_SCHEMA}.message m
    ON m._id = r.message_id
JOIN {config.RFX_MESSAGE_SCHEMA}.message_sender s
    ON s.message_id = m._id
   AND s._deleted IS NULL

LEFT JOIN thread_agg ta
    ON ta.thread_id = m.thread_id

LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_box mb
    ON mb._id = r.box_id
   AND mb._deleted IS NULL

LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_tag mt
    ON mt.resource = 'message_recipient'
   AND mt.resource_id = r._id
   AND mt._deleted IS NULL

LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = s.sender_id
   AND sp._deleted IS NULL

LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id
   AND rp._deleted IS NULL

WHERE
    r._deleted IS NULL
    AND NOT (
        s.sender_id = r.recipient_id
        AND s.box_id = r.box_id
    )

UNION ALL

-- ======================================================
-- ROOT: MESSAGE_SENDER
-- ======================================================
SELECT
    s._id,
    m._id AS message_id,
    m.thread_id,
    s.sender_id,

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
    m.expirable,
    m.priority,
    m.message_type,

    m.category,

    BOOL_OR(r.read)      AS is_read,
    MAX(r.mark_as_read) AS recipient_read_at,

    mb.key  AS box_key,
    mb.name AS box_name,
    mb.type AS box_type_enum,

    s._realm,
    s._created,
    s._updated,
    s._creator,
    s._updater,
    s._deleted,
    s._etag,

    s.sender_id AS target_profile_id,
    ta.message_count,
    'SENDER'::text AS root_type,
    s.direction,
    ARRAY_REMOVE(ARRAY[mt.key], NULL) AS tags


FROM {config.RFX_MESSAGE_SCHEMA}.message_sender s
JOIN {config.RFX_MESSAGE_SCHEMA}.message m
    ON m._id = s.message_id

LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON r.message_id = m._id
   AND r._deleted IS NULL

LEFT JOIN thread_agg ta
    ON ta.thread_id = m.thread_id

LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_box mb
    ON mb._id = s.box_id
   AND mb._deleted IS NULL

LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_tag mt
    ON mt.resource = 'message_sender'
   AND mt.resource_id = s._id
   AND mt._deleted IS NULL

LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = s.sender_id
   AND sp._deleted IS NULL

LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id
   AND rp._deleted IS NULL

WHERE s._deleted IS NULL

GROUP BY
    s._id,
    m._id,
    m.thread_id,
    s.sender_id,
    sp._id, sp.preferred_name, sp.name__given,
    sp.name__middle, sp.name__family,
    sp.name__prefix, sp.name__suffix,
    m.subject,
    m.content,
    m.content_type,
    m.expirable,
    m.priority,
    m.message_type,
    m.category,
    mb.key,
    mb.name,
    mb.type,
    s._realm,
    s._created,
    s._updated,
    s._creator,
    s._updater,
    s._deleted,
    s._etag,
    ta.message_count,
    tags
),
ranked AS (
    SELECT
        b.*,

        CASE
            WHEN b.direction = 'OUTBOUND' THEN
                ROW_NUMBER() OVER (
                    PARTITION BY b.thread_id, b.box_key
                    ORDER BY b._created ASC
                )
            ELSE 1
        END AS rn

    FROM base b
)

SELECT *
FROM ranked
WHERE
    (direction = 'OUTBOUND' AND rn = 1)
    OR direction = 'INBOUND';
    """,
)
