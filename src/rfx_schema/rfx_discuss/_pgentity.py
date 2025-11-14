"""
RFX Discuss PostgreSQL View Entities
=====================================
Registers database views for Alembic migrations.
"""

import os
from rfx_schema import logger
from rfx_base import config

from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities


# ============================================================================
# COMMENT VIEWS
# ============================================================================

comment_view = PGView(
    schema=config.RFX_DISCUSS_SCHEMA,
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
               FROM {config.RFX_DISCUSS_SCHEMA}.comment_attachment ca
              WHERE ca.comment_id = c._id AND ca._deleted IS NULL), 0::bigint) AS attachment_count,
        COALESCE(( SELECT count(*) AS count
               FROM {config.RFX_DISCUSS_SCHEMA}.comment_reaction cr
              WHERE cr.comment_id = c._id AND cr._deleted IS NULL), 0::bigint) AS reaction_count,
        COALESCE(( SELECT count(*) AS count
               FROM {config.RFX_DISCUSS_SCHEMA}.comment_flag cf
              WHERE cf.comment_id = c._id AND cf._deleted IS NULL), 0::bigint) AS flag_count
       FROM {config.RFX_DISCUSS_SCHEMA}.comment c
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = c._creator
      WHERE c._deleted IS NULL;
    """,
)

comment_attachment_view = PGView(
    schema=config.RFX_DISCUSS_SCHEMA,
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
       FROM {config.RFX_DISCUSS_SCHEMA}.comment_attachment ca
         JOIN "{config.RFX_MEDIA_SCHEMA}"."media-entry" me ON me._id = ca.media_entry_id
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = ca._creator
      WHERE ca._deleted IS NULL;
    """,
)

comment_reaction_view = PGView(
    schema=config.RFX_DISCUSS_SCHEMA,
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
       FROM {config.RFX_DISCUSS_SCHEMA}.comment_reaction cr
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = cr.user_id
      WHERE cr._deleted IS NULL;
    """,
)

comment_reaction_summary_view = PGView(
    schema=config.RFX_DISCUSS_SCHEMA,
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
       FROM {config.RFX_DISCUSS_SCHEMA}.comment_reaction cr
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = cr.user_id
      WHERE cr._deleted IS NULL
      GROUP BY cr.comment_id, cr.reaction_type;
    """,
)


# ============================================================================
# FLAG VIEWS
# ============================================================================

comment_flag_view = PGView(
    schema=config.RFX_DISCUSS_SCHEMA,
    signature="_comment_flag",
    definition=f"""
    SELECT cf._id,
        cf._created,
        cf._updated,
        cf._creator,
        cf._updater,
        cf._deleted,
        cf._etag,
        cf._realm,
        cf.comment_id,
        cf.reported_by_user_id,
        cf.reason,
        cf.status,
        cf.description,
        jsonb_build_object('id', reporter._id, 'name', COALESCE(reporter.preferred_name, ((reporter.name__given::text || ' '::text) || reporter.name__family::text)::character varying), 'avatar', reporter.picture_id) AS reporter,
        jsonb_build_object('id', c._id, 'content', "left"(c.content, 200), 'creator', jsonb_build_object('id', creator._id, 'name', COALESCE(creator.preferred_name, ((creator.name__given::text || ' '::text) || creator.name__family::text)::character varying))) AS comment_preview
       FROM {config.RFX_DISCUSS_SCHEMA}.comment_flag cf
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile reporter ON reporter._id = cf.reported_by_user_id
         LEFT JOIN {config.RFX_DISCUSS_SCHEMA}.comment c ON c._id = cf.comment_id
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile creator ON creator._id = c._creator
      WHERE cf._deleted IS NULL;
    """,
)

comment_flag_resolution_view = PGView(
    schema=config.RFX_DISCUSS_SCHEMA,
    signature="_comment_flag_resolution",
    definition=f"""
    SELECT cfr._id,
        cfr._created,
        cfr._updated,
        cfr._creator,
        cfr._updater,
        cfr._deleted,
        cfr._etag,
        cfr._realm,
        cfr.flag_id,
        cf.comment_id,
        cfr.resolved_by_user_id,
        cfr.resolved_at,
        cfr.resolution_note,
        cfr.resolution_action,
        jsonb_build_object('id', resolver._id, 'name', COALESCE(resolver.preferred_name, ((resolver.name__given::text || ' '::text) || resolver.name__family::text)::character varying), 'avatar', resolver.picture_id) AS resolver,
        jsonb_build_object('id', cf._id, 'comment_id', cf.comment_id, 'reason', cf.reason, 'status', cf.status, 'reported_by', jsonb_build_object('id', reporter._id, 'name', COALESCE(reporter.preferred_name, ((reporter.name__given::text || ' '::text) || reporter.name__family::text)::character varying))) AS flag_info
       FROM {config.RFX_DISCUSS_SCHEMA}.comment_flag_resolution cfr
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile resolver ON resolver._id = cfr.resolved_by_user_id
         LEFT JOIN {config.RFX_DISCUSS_SCHEMA}.comment_flag cf ON cf._id = cfr.flag_id
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile reporter ON reporter._id = cf.reported_by_user_id
      WHERE cfr._deleted IS NULL;
    """,
)

comment_flag_summary_view = PGView(
    schema=config.RFX_DISCUSS_SCHEMA,
    signature="_comment_flag_summary",
    definition=f"""
    SELECT cf.comment_id,
        count(*) AS total_flags,
        count(*) FILTER (WHERE cf.status::text = 'pending'::text) AS pending_flags,
        count(*) FILTER (WHERE cf.status::text = 'resolved'::text) AS resolved_flags,
        count(*) FILTER (WHERE cf.status::text = 'rejected'::text) AS rejected_flags,
        now() AS _created,
        now() AS _updated,
        NULL::uuid AS _creator,
        NULL::uuid AS _updater,
        NULL::timestamp with time zone AS _deleted,
        gen_random_uuid()::character varying AS _etag,
        NULL::character varying AS _realm,
        uuid_generate_v4() AS _id,
        jsonb_object_agg(cf.reason, ( SELECT count(*) AS count
               FROM {config.RFX_DISCUSS_SCHEMA}.comment_flag cf2
              WHERE cf2.comment_id = cf.comment_id AND cf2.reason::text = cf.reason::text AND cf2._deleted IS NULL)) AS flag_reasons,
        max(cf._created) AS latest_flag_at
       FROM {config.RFX_DISCUSS_SCHEMA}.comment_flag cf
      WHERE cf._deleted IS NULL
      GROUP BY cf.comment_id;
    """,
)


# ============================================================================
# SUBSCRIPTION VIEW
# ============================================================================

comment_subscription_view = PGView(
    schema=config.RFX_DISCUSS_SCHEMA,
    signature="_comment_subscription",
    definition=f"""
    SELECT cs._id,
        cs._created,
        cs._updated,
        cs._creator,
        cs._updater,
        cs._deleted,
        cs._etag,
        cs._realm,
        cs.comment_id,
        cs.user_id,
        cs.is_active,
        c.content AS comment_content,
        c._creator AS comment_creator_id,
        jsonb_build_object('id', p._id, 'name', COALESCE(p.preferred_name, ((p.name__given::text || ' '::text) || p.name__family::text)::character varying), 'avatar', p.picture_id) AS subscriber
       FROM {config.RFX_DISCUSS_SCHEMA}.comment_subscription cs
         JOIN {config.RFX_DISCUSS_SCHEMA}.comment c ON c._id = cs.comment_id
         LEFT JOIN {config.RFX_USER_SCHEMA}.profile p ON p._id = cs.user_id
      WHERE cs._deleted IS NULL;
    """,
)


# ============================================================================
# REGISTER ALL VIEWS
# ============================================================================


def register_pg_entities(allow):
    """Register all PostgreSQL views for Alembic migrations"""
    if not allow:
        logger.info("REGISTER_PG_ENTITIES is not set.")
        return

    register_entities(
        [
            # Comment views
            comment_view,
            comment_attachment_view,
            comment_reaction_view,
            comment_reaction_summary_view,
            # Flag views
            comment_flag_view,
            comment_flag_resolution_view,
            comment_flag_summary_view,
            # Subscription view
            comment_subscription_view,
        ]
    )

    logger.info(f"Registered 8 PostgreSQL views for {config.RFX_DISCUSS_SCHEMA} schema")


# Auto-register if environment variable is set
register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
