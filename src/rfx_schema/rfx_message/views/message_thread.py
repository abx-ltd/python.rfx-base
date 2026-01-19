from rfx_base import config
from alembic_utils.pg_view import PGView

message_thread_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_thread",
    definition=f"""
SELECT
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
    m.template_key,
    m.template_version,
    m.template_locale,
    m.template_engine,
    m.template_data,
    m.render_strategy,
    m.render_status,
    m.rendered_at,
    m.render_error,

    COUNT(*) OVER (PARTITION BY m.thread_id) AS message_count,

    /* ============================
       WHO CAN SEE THIS MESSAGE
       ============================ */
    ARRAY(
    SELECT DISTINCT uid FROM (

        -- sender
        SELECT s.sender_id AS uid

        UNION

        -- recipients (from table, not outer alias)
        SELECT mr.recipient_id AS uid
        FROM {config.RFX_MESSAGE_SCHEMA}.message_recipient mr
        WHERE
            mr.message_id = m._id
            AND mr._deleted IS NULL

    ) participants

    EXCEPT

    SELECT uid FROM (

        -- sender trashed
        SELECT ms.sender_id AS uid
        FROM {config.RFX_MESSAGE_SCHEMA}.message_sender ms
        JOIN {config.RFX_MESSAGE_SCHEMA}.message_box mb
            ON mb._id = ms.box_id
        WHERE
            ms.message_id = m._id
            AND mb.key = 'trashed'
            AND ms._deleted IS NULL

        UNION

        -- recipient trashed
        SELECT mr.recipient_id AS uid
        FROM {config.RFX_MESSAGE_SCHEMA}.message_recipient mr
        JOIN {config.RFX_MESSAGE_SCHEMA}.message_box mb
            ON mb._id = mr.box_id
        WHERE
            mr.message_id = m._id
            AND mb.key = 'trashed'
            AND mr._deleted IS NULL

    ) trashed_users
) AS visible_profile_ids,

    /* ============================
       DEFAULT AUDIT FIELDS
       ============================ */
    m._id,
    m._realm,
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag

FROM {config.RFX_MESSAGE_SCHEMA}.message m

JOIN {config.RFX_MESSAGE_SCHEMA}.message_sender s
    ON s.message_id = m._id
   AND s._deleted IS NULL

LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r
    ON r.message_id = m._id
   AND r._deleted IS NULL

LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp
    ON sp._id = s.sender_id
   AND sp._deleted IS NULL

LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp
    ON rp._id = r.recipient_id
   AND rp._deleted IS NULL

WHERE m._deleted IS NULL

GROUP BY
    m._id,
    m.thread_id,
    s.sender_id,

    sp._id,
    sp.preferred_name,
    sp.name__given,
    sp.name__middle,
    sp.name__family,
    sp.name__prefix,
    sp.name__suffix,

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
    m._created,
    m._updated,
    m._creator,
    m._updater,
    m._deleted,
    m._etag;
    """,
)
