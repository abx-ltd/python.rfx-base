"""
Ticket-related database views
"""

from alembic_utils.pg_view import PGView
from rfx_base import config

inquiry_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_inquiry",
    definition=f"""
    SELECT t._id,
        t._created,
        t._updated,
        t._creator,
        t._updater,
        t._deleted,
        t._etag,
        t._realm,
        t.title,
        t.description,
        t.priority,
        tt.key AS type,
        t.parent_id,
        t.assignee,
        t.status,
        t.availability,
        t.sync_status,
        t.organization_id,
        tt.icon_color AS type_icon_color,
        array_agg(DISTINCT tg.name) FILTER (WHERE tg.name IS NOT NULL) AS tag_names,
        t._updated AS activity,
        (ARRAY( SELECT DISTINCT jsonb_build_object('id', p._id, 'name', COALESCE(p.preferred_name, ((p.name__given::text || ' '::text) || p.name__family::text)::character varying), 'avatar', p.picture_id)::text AS jsonb_build_object
               FROM {config.RFX_CLIENT_SCHEMA}.ticket_participant tp2
                 JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = tp2.participant_id
              WHERE tp2.ticket_id = t._id AND p._id IS NOT NULL))::json[] AS participants
       FROM {config.RFX_CLIENT_SCHEMA}.ticket t
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.ticket_tag ttg ON ttg.ticket_id = t._id
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.tag tg ON tg._id = ttg.tag_id
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.ref__ticket_type tt ON tt.key::text = t.type::text
      WHERE t.is_inquiry = true
      GROUP BY t._id, t.title, t._updated, tt.key, tt.icon_color;
    """,
)

ticket_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_ticket",
    definition=f"""
    SELECT t._id,
        t._created,
        t._updated,
        t._creator,
        t._updater,
        t._deleted,
        t._etag,
        t._realm,
        t.title,
        t.description,
        t.priority,
        t.type,
        t.parent_id,
        t.assignee,
        t.status,
        t.availability,
        t.sync_status,
        t.organization_id,
        pt.project_id
       FROM {config.RFX_CLIENT_SCHEMA}.ticket t
         JOIN {config.RFX_CLIENT_SCHEMA}.project_ticket pt ON t._id = pt.ticket_id
      WHERE t.is_inquiry = false;
    """,
)
