from rfx_base import config
from alembic_utils.pg_view import PGView

message_box_view = PGView(
    schema=config.RFX_MESSAGE_SCHEMA,
    signature="_message_box",
    definition=f"""
WITH thread_agg AS (
         SELECT m.thread_id,
            count(*) AS message_count
           FROM {config.RFX_MESSAGE_SCHEMA}.message m
          WHERE m._deleted IS NULL
          GROUP BY m.thread_id
        ), base AS (
         SELECT r._id,
            m._id AS message_id,
            m.thread_id,
            s.sender_id,
            jsonb_build_object('id', sp._id, 'preferred_name', sp.preferred_name, 'given_name', sp.name__given, 'middle_name', sp.name__middle, 'family_name', sp.name__family, 'prefix', sp.name__prefix, 'suffix', sp.name__suffix) AS sender_profile,
            ARRAY[r.recipient_id] AS recipient_id,
            jsonb_build_object('id', rp._id, 'preferred_name', rp.preferred_name, 'given_name', rp.name__given, 'middle_name', rp.name__middle, 'family_name', rp.name__family, 'prefix', rp.name__prefix, 'suffix', rp.name__suffix) AS recipient_profile,
            m.subject,
            m.content,
            m.content_type,
            m.expirable,
            m.priority,
            m.message_type,
            m.category,
            r.read AS is_read,
            r.mark_as_read AS recipient_read_at,
            mb.key AS box_key,
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
            array_agg(DISTINCT t.key) FILTER (WHERE t.key IS NOT NULL) AS tags
           FROM {config.RFX_MESSAGE_SCHEMA}.message_recipient r
             JOIN {config.RFX_MESSAGE_SCHEMA}.message m ON m._id = r.message_id
             JOIN {config.RFX_MESSAGE_SCHEMA}.message_sender s ON s.message_id = m._id AND s._deleted IS NULL
             LEFT JOIN thread_agg ta ON ta.thread_id = m.thread_id
             LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_box mb ON mb._id = r.box_id AND mb._deleted IS NULL
             LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_tag mt ON mt.resource::text = 'message_recipient'::text AND mt.resource_id = r._id AND mt._deleted IS NULL
             LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.tag t ON t._id = mt.tag_id AND t._deleted IS NULL
             LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp ON sp._id = s.sender_id AND sp._deleted IS NULL
             LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp ON rp._id = r.recipient_id AND rp._deleted IS NULL
          WHERE r._deleted IS NULL AND NOT (s.sender_id = r.recipient_id AND s.box_id = r.box_id)
          GROUP BY r._id, m._id, m.thread_id, s.sender_id, sp._id, sp.preferred_name, sp.name__given, sp.name__middle, sp.name__family, sp.name__prefix, sp.name__suffix, r.recipient_id, rp._id, rp.preferred_name, rp.name__given, rp.name__middle, rp.name__family, rp.name__prefix, rp.name__suffix, m.subject, m.content, m.content_type, m.expirable, m.priority, m.message_type, m.category, r.read, r.mark_as_read, mb.key, mb.name, mb.type, r._realm, r._created, r._updated, r._creator, r._updater, r._deleted, r._etag, ta.message_count, r.direction
        UNION ALL
         SELECT s._id,
            m._id AS message_id,
            m.thread_id,
            s.sender_id,
            jsonb_build_object('id', sp._id, 'preferred_name', sp.preferred_name, 'given_name', sp.name__given, 'middle_name', sp.name__middle, 'family_name', sp.name__family, 'prefix', sp.name__prefix, 'suffix', sp.name__suffix) AS sender_profile,
            array_agg(DISTINCT r.recipient_id) FILTER (WHERE r.recipient_id IS NOT NULL) AS recipient_id,
            jsonb_agg(DISTINCT jsonb_build_object('id', rp._id, 'preferred_name', rp.preferred_name, 'given_name', rp.name__given, 'middle_name', rp.name__middle, 'family_name', rp.name__family, 'prefix', rp.name__prefix, 'suffix', rp.name__suffix)) FILTER (WHERE rp._id IS NOT NULL) AS recipient_profile,
            m.subject,
            m.content,
            m.content_type,
            m.expirable,
            m.priority,
            m.message_type,
            m.category,
            bool_or(r.read) AS is_read,
            max(r.mark_as_read) AS recipient_read_at,
            mb.key AS box_key,
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
            array_agg(DISTINCT t.key) FILTER (WHERE t.key IS NOT NULL) AS tags
           FROM {config.RFX_MESSAGE_SCHEMA}.message_sender s
             JOIN {config.RFX_MESSAGE_SCHEMA}.message m ON m._id = s.message_id
             LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_recipient r ON r.message_id = m._id AND r._deleted IS NULL
             LEFT JOIN thread_agg ta ON ta.thread_id = m.thread_id
             LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_box mb ON mb._id = s.box_id AND mb._deleted IS NULL
             LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.message_tag mt ON mt.resource::text = 'message_sender'::text AND mt.resource_id = s._id AND mt._deleted IS NULL
             LEFT JOIN {config.RFX_MESSAGE_SCHEMA}.tag t ON t._id = mt.tag_id AND t._deleted IS NULL
             LEFT JOIN {config.RFX_USER_SCHEMA}.profile sp ON sp._id = s.sender_id AND sp._deleted IS NULL
             LEFT JOIN {config.RFX_USER_SCHEMA}.profile rp ON rp._id = r.recipient_id AND rp._deleted IS NULL
          WHERE s._deleted IS NULL
          GROUP BY s._id, m._id, m.thread_id, s.sender_id, sp._id, sp.preferred_name, sp.name__given, sp.name__middle, sp.name__family, sp.name__prefix, sp.name__suffix, m.subject, m.content, m.content_type, m.expirable, m.priority, m.message_type, m.category, mb.key, mb.name, mb.type, s._realm, s._created, s._updated, s._creator, s._updater, s._deleted, s._etag, ta.message_count, s.direction
        ), ranked AS (
         SELECT b._id,
            b.message_id,
            b.thread_id,
            b.sender_id,
            b.sender_profile,
            b.recipient_id,
            b.recipient_profile,
            b.subject,
            b.content,
            b.content_type,
            b.expirable,
            b.priority,
            b.message_type,
            b.category,
            b.is_read,
            b.recipient_read_at,
            b.box_key,
            b.box_name,
            b.box_type_enum,
            b._realm,
            b._created,
            b._updated,
            b._creator,
            b._updater,
            b._deleted,
            b._etag,
            b.target_profile_id,
            b.message_count,
            b.root_type,
            b.direction,
            b.tags,
                CASE
                    WHEN b.direction = 'OUTBOUND'::{config.RFX_MESSAGE_SCHEMA}.directiontypeenum THEN row_number() OVER (PARTITION BY b.thread_id, b.box_key, b.target_profile_id ORDER BY b._created DESC)
                    ELSE 1::bigint
                END AS rn
           FROM base b
        )
 SELECT ranked._id,
    ranked.message_id,
    ranked.thread_id,
    ranked.sender_id,
    ranked.sender_profile,
    ranked.recipient_id,
    ranked.recipient_profile,
    ranked.subject,
    ranked.content,
    ranked.content_type,
    ranked.expirable,
    ranked.priority,
    ranked.message_type,
    ranked.category,
    ranked.is_read,
    ranked.recipient_read_at,
    ranked.box_key,
    ranked.box_name,
    ranked.box_type_enum,
    ranked._realm,
    ranked._created,
    ranked._updated,
    ranked._creator,
    ranked._updater,
    ranked._deleted,
    ranked._etag,
    ranked.target_profile_id,
    ranked.message_count,
    ranked.root_type,
    ranked.direction,
    ranked.tags,
    ranked.rn
   FROM ranked
  WHERE ranked.direction = 'OUTBOUND'::{config.RFX_MESSAGE_SCHEMA}.directiontypeenum AND ranked.rn = 1 OR ranked.direction = 'INBOUND'::{config.RFX_MESSAGE_SCHEMA}.directiontypeenum;
    """,
)
