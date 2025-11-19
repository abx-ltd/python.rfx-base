"""
Comment-related database views
"""

from alembic_utils.pg_view import PGView
from rfx_base import config

comment_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_comment",
    definition=f"""
    SELECT c._id,
        c._created,
        c._updated,
        c._creator,
        c._updater,
        c._deleted,
        c._etag,
        c._realm,
        c.master_id,
        c.parent_id,
        c.content,
        c.depth,
        c.organization_id,
        c.resource,
        c.resource_id,
        jsonb_build_object('id', p._id, 'name', COALESCE(p.preferred_name, ((p.name__given::text || ' '::text) || p.name__family::text)::character varying), 'avatar', p.picture_id) AS creator,
        COALESCE(( SELECT count(*) AS count
               FROM {config.RFX_CLIENT_SCHEMA}.comment_attachment ca
              WHERE ca.comment_id = c._id AND ca._deleted IS NULL), 0::bigint) AS attachment_count,
        COALESCE(( SELECT count(*) AS count
               FROM {config.RFX_CLIENT_SCHEMA}.comment_reaction cr
              WHERE cr.comment_id = c._id AND cr._deleted IS NULL), 0::bigint) AS reaction_count,
        c.source
       FROM {config.RFX_CLIENT_SCHEMA}.comment c
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = c._creator
      WHERE c._deleted IS NULL;
    """,
)

comment_attachment_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_comment_attachment",
    definition=f"""
    SELECT ca._id,
        ca._created,
        ca._updated,
        ca._creator,
        ca._updater,
        ca._deleted,
        ca._etag,
        ca._realm,
        ca.comment_id,
        ca.media_entry_id,
        ca.attachment_type,
        ca.caption,
        ca.display_order,
        ca.is_primary,
        me.filename,
        me.filehash,
        me.filemime,
        me.length,
        me.fspath,
        me.fskey,
        me.compress,
        me.cdn_url,
        me.resource,
        me.resource__id,
        jsonb_build_object('id', p._id, 'name', COALESCE(p.preferred_name, ((p.name__given::text || ' '::text) || p.name__family::text)::character varying), 'avatar', p.picture_id) AS uploader
       FROM {config.RFX_CLIENT_SCHEMA}.comment_attachment ca
         JOIN "{config.RFX_MEDIA_SCHEMA}"."media-entry" me ON me._id = ca.media_entry_id
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = ca._creator
      WHERE ca._deleted IS NULL;
    """,
)

comment_reaction_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_comment_reaction",
    definition=f"""
    SELECT cr._id,
        cr._created,
        cr._updated,
        cr._creator,
        cr._updater,
        cr._deleted,
        cr._etag,
        cr._realm,
        cr.comment_id,
        cr.user_id,
        cr.reaction_type,
        jsonb_build_object('id', p._id, 'name', COALESCE(p.preferred_name, ((p.name__given::text || ' '::text) || p.name__family::text)::character varying), 'avatar', p.picture_id) AS reactor
       FROM {config.RFX_CLIENT_SCHEMA}.comment_reaction cr
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = cr.user_id
      WHERE cr._deleted IS NULL;
    """,
)

comment_reaction_summary_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_comment_reaction_summary",
    definition=f"""
    SELECT cr.comment_id,
        cr.reaction_type,
        count(*) AS reaction_count,
        jsonb_agg(jsonb_build_object('id', p._id, 'name', COALESCE(p.preferred_name, ((p.name__given::text || ' '::text) || p.name__family::text)::character varying), 'avatar', p.picture_id) ORDER BY cr._created) AS users,
        now() AS _created,
        now() AS _updated,
        NULL::uuid AS _creator,
        NULL::uuid AS _updater,
        NULL::timestamp with time zone AS _deleted,
        gen_random_uuid()::character varying AS _etag,
        NULL::character varying AS _realm,
        uuid_generate_v4() AS _id
       FROM {config.RFX_CLIENT_SCHEMA}.comment_reaction cr
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = cr.user_id
      WHERE cr._deleted IS NULL
      GROUP BY cr.comment_id, cr.reaction_type;
    """,
)
