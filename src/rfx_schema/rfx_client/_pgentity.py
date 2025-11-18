"""
RFX Client PostgreSQL View Entities
====================================
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


# ============================================================================
# CREDIT VIEWS
# ============================================================================


credit_summary_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_credit_summary",
    definition=f"""
    SELECT uuid_generate_v4() AS _id,
        cb._created,
        cb._updated,
        cb._creator,
        cb._updater,
        cb._deleted,
        cb._etag,
        cb._realm,
        cb.organization_id,
        cb.ar_credits AS current_ar_credits,
        cb.de_credits AS current_de_credits,
        cb.op_credits AS current_op_credits,
        cb.total_credits AS current_total_credits,
        cb.total_purchased_credits,
        cb.total_used,
        cb.total_refunded_credits,
        cb.total_purchased_credits - cb.total_used AS remaining_credits,
            CASE
                WHEN cb.total_purchased_credits > 0::numeric THEN round((cb.total_purchased_credits - cb.total_used) / cb.total_purchased_credits * 100::numeric, 2)
                ELSE 0::numeric
            END AS remaining_percentage,
        COALESCE(cb.avg_daily_usage, 0::numeric) AS avg_daily_usage,
        COALESCE(cb.avg_weekly_usage, 0::numeric) AS avg_weekly_usage,
        cb.days_until_depleted,
        COALESCE(month_purchase.total, 0::numeric) AS month_purchased,
        COALESCE(month_usage.total, 0::numeric) AS month_used,
        cb.last_purchase_date,
        cb.last_usage_date,
        now() AS last_updated
       FROM {config.RFX_CLIENT_SCHEMA}.credit_balance cb
         LEFT JOIN ( SELECT credit_purchase.organization_id,
                sum(credit_purchase.total_credits) AS total
               FROM {config.RFX_CLIENT_SCHEMA}.credit_purchase
              WHERE date_trunc('month'::text, credit_purchase.purchase_date) = date_trunc('month'::text, CURRENT_DATE::timestamp with time zone) 
                AND credit_purchase.status::text = 'COMPLETED'::text 
                AND credit_purchase._deleted IS NULL
              GROUP BY credit_purchase.organization_id) month_purchase ON cb.organization_id = month_purchase.organization_id
         LEFT JOIN ( SELECT credit_usage_log.organization_id,
                sum(credit_usage_log.credits_used) AS total
               FROM {config.RFX_CLIENT_SCHEMA}.credit_usage_log
              WHERE date_trunc('month'::text, credit_usage_log.usage_date) = date_trunc('month'::text, CURRENT_DATE::timestamp with time zone) 
                AND credit_usage_log._deleted IS NULL
              GROUP BY credit_usage_log.organization_id) month_usage ON cb.organization_id = month_usage.organization_id
      WHERE cb._deleted IS NULL;
    """,
)

credit_usage_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_credit_usage",
    definition=f"""
    SELECT p._id,
        p._created,
        p._creator,
        p._deleted,
        p._etag,
        p._updated,
        p._realm,
        p.organization_id,
        EXTRACT(isoyear FROM activity_log_entry._created) AS usage_year,
        EXTRACT(week FROM activity_log_entry._created) AS usage_week,
        EXTRACT(month FROM activity_log_entry._created) AS usage_month,
        date_trunc('week'::text, activity_log_entry._created)::date AS week_start_date,
        COALESCE(sum(
            CASE
                WHEN rwt.alias::text = 'AR'::text THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                ELSE 0::numeric
            END), 0::numeric) AS ar_credits,
        COALESCE(sum(
            CASE
                WHEN rwt.alias::text = 'DE'::text THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                ELSE 0::numeric
            END), 0::numeric) AS de_credits,
        COALESCE(sum(
            CASE
                WHEN rwt.alias::text = 'OP'::text THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                ELSE 0::numeric
            END), 0::numeric) AS op_credits,
        COALESCE(sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric), 0::numeric) AS total_credits
       FROM {config.RFX_CLIENT_SCHEMA}.project p
         JOIN LATERAL ( SELECT al._created
               FROM "{config.RFX_AUDIT_SCHEMA}"."activity-log" al
              WHERE al.identifier = p._id 
                AND al.resource::text = 'project'::text 
                AND al.msglabel::text = 'create-project'::text
              ORDER BY al._created
             LIMIT 1) activity_log_entry ON true
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package pwp ON p._id = pwp.project_id AND pwp._deleted IS NULL
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi ON pwp._id = pwpwi.project_work_package_id AND pwpwi._deleted IS NULL
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id AND pwi._deleted IS NULL
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.ref__work_item_type rwt ON pwi.type::text = rwt.key::text
      WHERE p.status::text = 'ACTIVE'::text AND activity_log_entry._created IS NOT NULL
      GROUP BY p._id, p._created, p._creator, p._deleted, p._etag, p._updated, p._realm, 
               (EXTRACT(isoyear FROM activity_log_entry._created)), 
               (EXTRACT(week FROM activity_log_entry._created)), 
               (EXTRACT(month FROM activity_log_entry._created)), 
               (date_trunc('week'::text, activity_log_entry._created))
      ORDER BY (EXTRACT(isoyear FROM activity_log_entry._created)) DESC, 
               (EXTRACT(week FROM activity_log_entry._created)) DESC;
    """,
)


# ============================================================================
# PROJECT VIEWS
# ============================================================================

project_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_project",
    definition=f"""
    SELECT p._id,
        p._created,
        p._updated,
        p._creator,
        p._updater,
        p._deleted,
        p._etag,
        p._realm,
        p.name,
        p.description,
        p.category,
        p.priority,
        p.status,
        p.start_date,
        p.target_date,
        p.duration,
        p.duration_text,
        p.free_credit_applied,
        p.referral_code_used,
        p.sync_status,
        p.organization_id,
        COALESCE(array_agg(pm.member_id) FILTER (WHERE pm._deleted IS NULL), '{{}}'::uuid[]) AS members,
        round(COALESCE(( SELECT sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric) AS sum
               FROM {config.RFX_CLIENT_SCHEMA}.project_work_package pwp
                 JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi ON pwp._id = pwpwi.project_work_package_id AND pwpwi._deleted IS NULL
                 JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id AND pwi._deleted IS NULL
              WHERE pwp.project_id = p._id AND pwp._deleted IS NULL), 0::numeric), 2) AS total_credit,
        round(COALESCE(( SELECT sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric) AS sum
               FROM {config.RFX_CLIENT_SCHEMA}.project_work_package pwp
                 JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi ON pwp._id = pwpwi.project_work_package_id AND pwpwi._deleted IS NULL
                 JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id AND pwi._deleted IS NULL
              WHERE pwp.project_id = p._id AND pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum AND pwp._deleted IS NULL), 0::numeric), 2) AS used_credit
       FROM {config.RFX_CLIENT_SCHEMA}.project p
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_member pm ON pm.project_id = p._id
      WHERE p._deleted IS NULL
      GROUP BY p._id;
    """,
)

project_credit_summary_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_project_credit_summary",
    definition=f"""
    SELECT p._id,
        p._created,
        p._updated,
        p._creator,
        p._updater,
        p._deleted,
        p._etag,
        p._realm,
        p._id AS project_id,
        p.organization_id,
        p.name AS project_name,
        p.status AS project_status,
        round(COALESCE(sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric), 0::numeric), 2) AS total_credits,
        round(COALESCE(sum(
            CASE
                WHEN pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                ELSE 0::numeric
            END), 0::numeric), 2) AS credit_used,
        round(COALESCE(( SELECT sum(cul.credits_used) AS sum
               FROM {config.RFX_CLIENT_SCHEMA}.credit_usage_log cul
              WHERE cul.project_id = p._id AND cul._deleted IS NULL), 0::numeric), 2) AS actual_total_credits,
        round(COALESCE(sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric), 0::numeric) - COALESCE(sum(
            CASE
                WHEN pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                ELSE 0::numeric
            END), 0::numeric), 2) AS credits_remaining,
            CASE
                WHEN COALESCE(sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric), 0::numeric) > 0::numeric THEN round(COALESCE(sum(
                CASE
                    WHEN pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                    ELSE 0::numeric
                END), 0::numeric) / sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric) * 100::numeric, 2)
                ELSE 0::numeric
            END AS completion_percentage,
        count(DISTINCT pwp._id)::integer AS total_work_packages,
        count(DISTINCT
            CASE
                WHEN pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN pwp._id
                ELSE NULL::uuid
            END)::integer AS completed_work_packages,
        count(DISTINCT pwi._id)::integer AS total_work_items
       FROM {config.RFX_CLIENT_SCHEMA}.project p
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package pwp ON p._id = pwp.project_id AND pwp._deleted IS NULL
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi ON pwp._id = pwpwi.project_work_package_id AND pwpwi._deleted IS NULL
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id AND pwi._deleted IS NULL
      WHERE p._deleted IS NULL
      GROUP BY p._id, p.name, p.organization_id, p.status
      ORDER BY p.organization_id, p.name;
    """,
)


# ============================================================================
# WORK PACKAGE VIEWS
# ============================================================================

work_package_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_work_package",
    definition=f"""
    WITH work_items AS (
             SELECT link.work_package_id,
                wi_1._id AS work_item_id,
                wi_1.type,
                wi_1.price_unit,
                wi_1.credit_per_unit,
                wi_1.price_unit * wi_1.credit_per_unit AS total_credits,
                wi_1.price_unit * wi_1.credit_per_unit * 30.0 AS total_cost,
                rt.alias AS type_alias
               FROM {config.RFX_CLIENT_SCHEMA}.work_package_work_item link
                 JOIN {config.RFX_CLIENT_SCHEMA}.work_item wi_1 ON wi_1._id = link.work_item_id AND wi_1._deleted IS NULL
                 LEFT JOIN {config.RFX_CLIENT_SCHEMA}.ref__work_item_type rt ON wi_1.type::text = rt.key::text
              WHERE link._deleted IS NULL
            )
     SELECT wp._id,
        wp._created,
        wp._updated,
        wp._creator,
        wp._updater,
        wp._deleted,
        wp._etag,
        wp._realm,
        wp.organization_id,
        wp.work_package_name,
        wp.description,
        wp.example_description,
        wp.complexity_level,
        wp.estimate,
        wp.organization_id IS NOT NULL AS is_custom,
        array_agg(DISTINCT wi.type_alias)::character varying(50)[] AS type_list,
        count(DISTINCT wi.work_item_id) AS work_item_count,
        sum(wi.total_credits) AS credits,
        sum(wi.total_credits) FILTER (WHERE wi.type::text = 'ARCHITECTURE'::text) AS architectural_credits,
        sum(wi.total_credits) FILTER (WHERE wi.type::text = 'DEVELOPMENT'::text) AS development_credits,
        sum(wi.total_credits) FILTER (WHERE wi.type::text = 'OPERATION'::text) AS operation_credits,
        sum(wi.total_cost) FILTER (WHERE wi.type::text = ANY (ARRAY['ARCHITECTURE'::text, 'DEVELOPMENT'::text])) AS upfront_cost,
        sum(wi.total_cost) FILTER (WHERE wi.type::text = 'OPERATION'::text) AS monthly_cost
       FROM {config.RFX_CLIENT_SCHEMA}.work_package wp
         LEFT JOIN work_items wi ON wi.work_package_id = wp._id
      WHERE wp._deleted IS NULL
      GROUP BY wp._id, wp._created, wp._updated, wp._creator, wp._updater, wp._deleted, wp._etag, wp._realm, 
               wp.organization_id, wp.work_package_name, wp.description, wp.example_description, wp.complexity_level, wp.estimate;
    """,
)

project_work_package_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_project_work_package",
    definition=f"""
    WITH work_items AS (
             SELECT link.project_work_package_id,
                wi_1._id AS project_work_item_id,
                wi_1.type,
                wi_1.price_unit,
                wi_1.credit_per_unit,
                wi_1.price_unit * wi_1.credit_per_unit AS total_credits,
                wi_1.price_unit * wi_1.credit_per_unit * 30.0 AS total_cost
               FROM {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item link
                 JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item wi_1 ON wi_1._id = link.project_work_item_id AND wi_1._deleted IS NULL
              WHERE link._deleted IS NULL
            ), deliverable_counts AS (
             SELECT d.project_work_item_id,
                count(DISTINCT d._id) AS deliverable_count
               FROM {config.RFX_CLIENT_SCHEMA}.project_work_item_deliverable d
              WHERE d._deleted IS NULL
              GROUP BY d.project_work_item_id
            )
     SELECT pwp._id,
        pwp._created,
        pwp._updated,
        pwp._creator,
        pwp._updater,
        pwp._deleted,
        pwp._etag,
        pwp._realm,
        pwp.project_id,
        pwp.work_package_id,
        pwp.quantity,
        p.status,
        pwp.work_package_name,
        pwp.work_package_is_custom,
        pwp.work_package_description,
        pwp.work_package_example_description,
        pwp.work_package_complexity_level,
        pwp.work_package_estimate,
        array_agg(DISTINCT rwt.alias)::character varying(50)[] AS type_list,
        count(DISTINCT wi.project_work_item_id) AS work_item_count,
        COALESCE(sum(wi.total_credits), 0::numeric) AS credits,
        COALESCE(sum(wi.total_credits) FILTER (WHERE upper(wi.type::text) = 'ARCHITECTURE'::text), 0::numeric) AS architectural_credits,
        COALESCE(sum(wi.total_credits) FILTER (WHERE upper(wi.type::text) = 'DEVELOPMENT'::text), 0::numeric) AS development_credits,
        COALESCE(sum(wi.total_credits) FILTER (WHERE upper(wi.type::text) = 'OPERATION'::text), 0::numeric) AS operation_credits,
        COALESCE(sum(wi.total_cost) FILTER (WHERE upper(wi.type::text) = ANY (ARRAY['ARCHITECTURE'::text, 'DEVELOPMENT'::text])), 0::numeric) AS upfront_cost,
        COALESCE(sum(wi.total_cost) FILTER (WHERE upper(wi.type::text) = 'OPERATION'::text), 0::numeric) AS monthly_cost,
        COALESCE(sum(dc.deliverable_count), 0::numeric) AS total_deliverables
       FROM {config.RFX_CLIENT_SCHEMA}.project_work_package pwp
         JOIN {config.RFX_CLIENT_SCHEMA}.project p ON p._id = pwp.project_id
         LEFT JOIN work_items wi ON wi.project_work_package_id = pwp._id
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.ref__work_item_type rwt ON wi.type::text = rwt.key::text
         LEFT JOIN deliverable_counts dc ON dc.project_work_item_id = wi.project_work_item_id
      WHERE pwp._deleted IS NULL
      GROUP BY pwp._id, pwp.project_id, pwp.work_package_id, pwp.quantity, pwp.work_package_name, 
               pwp.work_package_is_custom, pwp.work_package_estimate, p.status;
    """,
)

work_package_credit_usage_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_work_package_credit_usage",
    definition=f"""
    WITH wp_usage AS (
             SELECT cul.work_package_id,
                cul.project_id,
                cul.organization_id,
                sum(
                    CASE
                        WHEN cul.work_type::text = 'ARCHITECTURE'::text THEN cul.credits_used
                        ELSE 0::numeric
                    END) AS actual_ar,
                sum(
                    CASE
                        WHEN cul.work_type::text = 'DEVELOPMENT'::text THEN cul.credits_used
                        ELSE 0::numeric
                    END) AS actual_de,
                sum(
                    CASE
                        WHEN cul.work_type::text = 'OPERATION'::text THEN cul.credits_used
                        ELSE 0::numeric
                    END) AS actual_op,
                sum(cul.credits_used) AS actual_total,
                min(cul._created) AS first_created,
                max(cul._updated) AS last_updated
               FROM {config.RFX_CLIENT_SCHEMA}.credit_usage_log cul
              WHERE cul._deleted IS NULL
              GROUP BY cul.work_package_id, cul.project_id, cul.organization_id
            ), wp_info AS (
             SELECT pwp.work_package_id,
                pwp.project_id,
                pwp.work_package_name,
                vwp.architectural_credits * pwp.quantity::numeric AS estimated_ar,
                vwp.development_credits * pwp.quantity::numeric AS estimated_de,
                vwp.operation_credits * pwp.quantity::numeric AS estimated_op,
                vwp.credits * pwp.quantity::numeric AS estimated_total,
                vwp.status,
                vwp.work_item_count AS total_work_items,
                    CASE
                        WHEN vwp.status::text = 'COMPLETED'::text THEN 100
                        WHEN vwp.status::text = 'IN_PROGRESS'::text THEN 50
                        ELSE 0
                    END AS completion_percentage,
                pwp._created,
                pwp._updated
               FROM {config.RFX_CLIENT_SCHEMA}.project_work_package pwp
                 LEFT JOIN {config.RFX_CLIENT_SCHEMA}._project_work_package vwp ON pwp.work_package_id = vwp.work_package_id AND pwp.project_id = vwp.project_id
              WHERE pwp._deleted IS NULL
            ), wi_stats AS (
             SELECT pwp.work_package_id,
                pwp.project_id,
                count(DISTINCT pwi.project_work_item_id)::integer AS completed_work_items
               FROM {config.RFX_CLIENT_SCHEMA}.project_work_package pwp
                 JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwi ON pwp._id = pwi.project_work_package_id
                 JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item item ON pwi.project_work_item_id = item._id
              WHERE item._deleted IS NULL AND pwp._deleted IS NULL
              GROUP BY pwp.work_package_id, pwp.project_id
            )
     SELECT wpi.work_package_id AS _id,
        COALESCE(wpu.first_created, wpi._created) AS _created,
        COALESCE(wpu.last_updated, wpi._updated) AS _updated,
        NULL::uuid AS _creator,
        NULL::uuid AS _updater,
        NULL::timestamp with time zone AS _deleted,
        gen_random_uuid()::character varying AS _etag,
        NULL::character varying AS _realm,
        wpi.work_package_id,
        wpi.project_id,
        COALESCE(wpu.organization_id, p.organization_id) AS organization_id,
        wpi.work_package_name,
        round(COALESCE(wpi.estimated_ar, 0::numeric), 2) AS estimated_ar_credits,
        round(COALESCE(wpi.estimated_de, 0::numeric), 2) AS estimated_de_credits,
        round(COALESCE(wpi.estimated_op, 0::numeric), 2) AS estimated_op_credits,
        round(COALESCE(wpi.estimated_total, 0::numeric), 2) AS estimated_total_credits,
        round(COALESCE(wpu.actual_ar, 0::numeric), 2) AS actual_ar_credits,
        round(COALESCE(wpu.actual_de, 0::numeric), 2) AS actual_de_credits,
        round(COALESCE(wpu.actual_op, 0::numeric), 2) AS actual_op_credits,
        round(COALESCE(wpu.actual_total, 0::numeric), 2) AS actual_total_credits,
        round(COALESCE(wpu.actual_ar, 0::numeric) - COALESCE(wpi.estimated_ar, 0::numeric), 2) AS variance_ar,
        round(COALESCE(wpu.actual_de, 0::numeric) - COALESCE(wpi.estimated_de, 0::numeric), 2) AS variance_de,
        round(COALESCE(wpu.actual_op, 0::numeric) - COALESCE(wpi.estimated_op, 0::numeric), 2) AS variance_op,
        round(COALESCE(wpu.actual_total, 0::numeric) - COALESCE(wpi.estimated_total, 0::numeric), 2) AS variance_total,
            CASE
                WHEN COALESCE(wpi.estimated_total, 0::numeric) > 0::numeric THEN round((wpu.actual_total - wpi.estimated_total) / wpi.estimated_total * 100::numeric, 2)
                ELSE 0::numeric
            END AS variance_percentage,
        round(wpi.completion_percentage::numeric, 2) AS completion_percentage,
        round(COALESCE(wpi.estimated_total, 0::numeric) - COALESCE(wpu.actual_total, 0::numeric), 2) AS credits_remaining,
        COALESCE(wpi.total_work_items, 0::bigint)::integer AS total_work_items,
        COALESCE(wis.completed_work_items, 0) AS completed_work_items,
        COALESCE(wpi.status, 'PENDING'::character varying) AS status
       FROM wp_info wpi
         LEFT JOIN wp_usage wpu ON wpi.work_package_id = wpu.work_package_id AND wpi.project_id = wpu.project_id
         LEFT JOIN wi_stats wis ON wpi.work_package_id = wis.work_package_id AND wpi.project_id = wis.project_id
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project p ON wpi.project_id = p._id
      ORDER BY wpi.project_id, wpi.work_package_name;
    """,
)


# ============================================================================
# WORK ITEM VIEWS
# ============================================================================

work_item_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_work_item",
    definition=f"""
    SELECT wi._id,
        wi._created,
        wi._updated,
        wi._creator,
        wi._updater,
        wi._deleted,
        wi._etag,
        wi._realm,
        wi.organization_id,
        wi.type,
        wi.name,
        wi.description,
        wi.price_unit,
        wi.credit_per_unit,
        wi.estimate,
        rt.alias AS type_alias
       FROM {config.RFX_CLIENT_SCHEMA}.work_item wi
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.ref__work_item_type rt ON wi.type::text = rt.key::text
      WHERE wi._deleted IS NULL;
    """,
)

work_item_listing_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_work_item_listing",
    definition=f"""
    SELECT wpwi._id,
        wpwi._created,
        wpwi._updated,
        wpwi._creator,
        wpwi._updater,
        wpwi._deleted,
        wpwi._etag,
        wpwi._realm,
        wpwi.work_package_id,
        wpwi.work_item_id,
        wi.name AS work_item_name,
        wi.description AS work_item_description,
        wi.organization_id,
        COALESCE(wi.price_unit, 0::numeric) AS price_unit,
        COALESCE(wi.credit_per_unit, 0::numeric) AS credit_per_unit,
        wi.type AS work_item_type_code,
        rwt.alias AS work_item_type_alias,
        COALESCE(wi.price_unit, 0::numeric) * COALESCE(wi.credit_per_unit, 0::numeric) AS total_credits_for_item,
        COALESCE(wi.price_unit, 0::numeric) * COALESCE(wi.credit_per_unit, 0::numeric) * 30.0 AS estimated_cost_for_item,
        wi.estimate
       FROM {config.RFX_CLIENT_SCHEMA}.work_package_work_item wpwi
         JOIN {config.RFX_CLIENT_SCHEMA}.work_item wi ON wpwi.work_item_id = wi._id AND wi._deleted IS NULL
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.ref__work_item_type rwt ON wi.type::text = rwt.key::text
      WHERE wpwi._deleted IS NULL;
    """,
)

project_work_item_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_project_work_item",
    definition=f"""
    SELECT pwi._id,
        pwi._created,
        pwi._updated,
        pwi._creator,
        pwi._updater,
        pwi._deleted,
        pwi._etag,
        pwi._realm,
        pwi.type,
        pwi.name,
        pwi.description,
        pwi.price_unit,
        pwi.credit_per_unit,
        pwi.estimate,
        rt.alias AS type_alias
       FROM {config.RFX_CLIENT_SCHEMA}.project_work_item pwi
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.ref__work_item_type rt ON pwi.type::text = rt.key::text
      WHERE pwi._deleted IS NULL;
    """,
)

project_work_item_listing_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_project_work_item_listing",
    definition=f"""
    SELECT pwpwi._id,
        pwpwi._created,
        pwpwi._updated,
        pwpwi._creator,
        pwpwi._updater,
        pwpwi._deleted,
        pwpwi._etag,
        pwpwi._realm,
        pwpwi.project_work_package_id,
        pwpwi.project_work_item_id,
        pwi.name AS project_work_item_name,
        pwi.description AS project_work_item_description,
        COALESCE(pwi.price_unit, 0::numeric) AS price_unit,
        COALESCE(pwi.credit_per_unit, 0::numeric) AS credit_per_unit,
        pwi.type AS project_work_item_type_code,
        rwt.alias AS project_work_item_type_alias,
        COALESCE(pwi.price_unit, 0::numeric) * COALESCE(pwi.credit_per_unit, 0::numeric) AS total_credits_for_item,
        COALESCE(pwi.price_unit, 0::numeric) * COALESCE(pwi.credit_per_unit, 0::numeric) * 30.0 AS estimated_cost_for_item,
        pwi.estimate
       FROM {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi
         JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id AND pwi._deleted IS NULL
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.ref__work_item_type rwt ON pwi.type::text = rwt.key::text
      WHERE pwpwi._deleted IS NULL;
    """,
)

project_document_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_project_document",
    definition=f"""
    SELECT pd._id,
        pd._created,
        pd._updated,
        pd._creator,
        pd._updater,
        pd._deleted,
        pd._etag,
        pd._realm,
        pd.name AS document_name,
        pd.description,
        pd.doc_type,
        pd.file_size,
        pd.status,
        pd.project_id,
        p.name AS project_name,
        p.status AS project_status,
        pd.organization_id,
        pd.media_entry_id,
        me.filename,
        me.filemime,
        me.fspath,
        me.cdn_url,
        me.length AS file_length,
        jsonb_build_object(
            'id', creator._id, 
            'name', COALESCE(
                creator.preferred_name, 
                ((creator.name__given::text || ' '::text) || creator.name__family::text)::character varying
            ), 
            'avatar', creator.picture_id
        ) AS created_by,
        COALESCE(
            (
                SELECT json_agg(
                    jsonb_build_object(
                        'id', part._id, 
                        'name', COALESCE(
                            part.preferred_name, 
                            ((part.name__given::text || ' '::text) || part.name__family::text)::character varying
                        ), 
                        'avatar', part.picture_id, 
                        'role', pdp.role
                    )
                ) AS json_agg
                FROM {config.RFX_CLIENT_SCHEMA}.project_document_participant pdp
                JOIN {config.RFX_USER_SCHEMA}.profile part ON part._id = pdp.participant_id
                WHERE pdp.document_id = pd._id 
                  AND pdp._deleted IS NULL
            ), 
            '[]'::json
        ) AS participants,
        COALESCE(
            (
                SELECT count(DISTINCT pdp.participant_id) AS count
                FROM {config.RFX_CLIENT_SCHEMA}.project_document_participant pdp
                WHERE pdp.document_id = pd._id 
                  AND pdp._deleted IS NULL
            ), 
            0::bigint
        )::integer AS participant_count,
        GREATEST(pd._created, pd._updated) AS activity
    FROM {config.RFX_CLIENT_SCHEMA}.project_document pd
    JOIN {config.RFX_CLIENT_SCHEMA}.project p 
        ON pd.project_id = p._id 
        AND p._deleted IS NULL
    LEFT JOIN "{config.RFX_MEDIA_SCHEMA}"."media-entry" me 
        ON pd.media_entry_id = me._id
    LEFT JOIN {config.RFX_USER_SCHEMA}.profile creator 
        ON pd._creator = creator._id
    WHERE pd._deleted IS NULL
    ORDER BY pd.organization_id, pd.project_id, pd._created DESC;
    """,
)


# ============================================================================
# TICKET VIEWS
# ============================================================================

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


# ============================================================================
# ORGANIZATION VIEWS
# ============================================================================

organization_credit_summary_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_organization_credit_summary",
    definition=f"""
    WITH project_credit_calc AS (
             SELECT p.organization_id,
                sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric) AS total_allocated,
                sum(
                    CASE
                        WHEN pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS total_used,
                sum(
                    CASE
                        WHEN pwi.type::text = 'ARCHITECTURE'::text THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS ar_allocated,
                sum(
                    CASE
                        WHEN pwi.type::text = 'ARCHITECTURE'::text AND pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS ar_used,
                sum(
                    CASE
                        WHEN pwi.type::text = 'DEVELOPMENT'::text THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS de_allocated,
                sum(
                    CASE
                        WHEN pwi.type::text = 'DEVELOPMENT'::text AND pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS de_used,
                sum(
                    CASE
                        WHEN pwi.type::text = 'OPERATION'::text THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS op_allocated,
                sum(
                    CASE
                        WHEN pwi.type::text = 'OPERATION'::text AND pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS op_used
               FROM {config.RFX_CLIENT_SCHEMA}.project p
                 LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package pwp ON p._id = pwp.project_id AND pwp._deleted IS NULL
                 LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi ON pwp._id = pwpwi.project_work_package_id AND pwpwi._deleted IS NULL
                 LEFT JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id AND pwi._deleted IS NULL
              WHERE p._deleted IS NULL
              GROUP BY p.organization_id
            ), project_counts AS (
             SELECT project.organization_id,
                count(*) AS total_projects,
                count(
                    CASE
                        WHEN project.status::text = 'ACTIVE'::text THEN 1
                        ELSE NULL::integer
                    END) AS active_projects
               FROM {config.RFX_CLIENT_SCHEMA}.project
              WHERE project._deleted IS NULL
              GROUP BY project.organization_id
            )
     SELECT org._id,
        org._created,
        org._updated,
        org._creator,
        org._updater,
        org._deleted,
        org._etag,
        org._realm,
        org._id AS organization_id,
        round(COALESCE(cb.total_credits, 0::numeric), 2) AS total_credits,
        round(COALESCE(cb.total_purchased_credits, 0::numeric), 2) AS total_purchased_credits,
        round(COALESCE(pc.total_allocated, 0::numeric), 2) AS total_allocated,
        round(COALESCE(pc.total_used, 0::numeric), 2) AS total_used,
        round(COALESCE(cb.total_credits, 0::numeric) - COALESCE(pc.total_allocated, 0::numeric), 2) AS total_available,
        round(COALESCE(cb.ar_credits, 0::numeric), 2) AS ar_credits_balance,
        round(COALESCE(pc.ar_allocated, 0::numeric), 2) AS ar_credits_allocated,
        round(COALESCE(pc.ar_used, 0::numeric), 2) AS ar_credits_used,
        round(COALESCE(cb.ar_credits, 0::numeric) - COALESCE(pc.ar_allocated, 0::numeric), 2) AS ar_credits_available,
        round(COALESCE(cb.de_credits, 0::numeric), 2) AS de_credits_balance,
        round(COALESCE(pc.de_allocated, 0::numeric), 2) AS de_credits_allocated,
        round(COALESCE(pc.de_used, 0::numeric), 2) AS de_credits_used,
        round(COALESCE(cb.de_credits, 0::numeric) - COALESCE(pc.de_allocated, 0::numeric), 2) AS de_credits_available,
        round(COALESCE(cb.op_credits, 0::numeric), 2) AS op_credits_balance,
        round(COALESCE(pc.op_allocated, 0::numeric), 2) AS op_credits_allocated,
        round(COALESCE(pc.op_used, 0::numeric), 2) AS op_credits_used,
        round(COALESCE(cb.op_credits, 0::numeric) - COALESCE(pc.op_allocated, 0::numeric), 2) AS op_credits_available,
            CASE
                WHEN COALESCE(cb.total_credits, 0::numeric) > 0::numeric THEN round(COALESCE(pc.total_allocated, 0::numeric) / cb.total_credits * 100::numeric, 2)
                ELSE 0::numeric
            END AS allocation_percentage,
            CASE
                WHEN COALESCE(pc.total_allocated, 0::numeric) > 0::numeric THEN round(COALESCE(pc.total_used, 0::numeric) / pc.total_allocated * 100::numeric, 2)
                ELSE 0::numeric
            END AS completion_percentage,
        COALESCE(p_count.total_projects, 0::bigint)::integer AS total_projects,
        COALESCE(p_count.active_projects, 0::bigint)::integer AS active_projects,
        COALESCE(cb.is_low_balance, false) AS is_low_balance,
        round(COALESCE(cb.low_balance_threshold, 100::numeric), 2) AS low_balance_threshold
       FROM {config.RFX_USER_SCHEMA}.organization org
         LEFT JOIN {config.RFX_CLIENT_SCHEMA}.credit_balance cb ON org._id = cb.organization_id AND cb._deleted IS NULL
         LEFT JOIN project_credit_calc pc ON org._id = pc.organization_id
         LEFT JOIN project_counts p_count ON org._id = p_count.organization_id
      WHERE org._deleted IS NULL
      ORDER BY org._id;
    """,
)

organization_weekly_credit_usage_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_organization_weekly_credit_usage",
    definition=f"""
    WITH done_work_packages AS (
             SELECT p.organization_id,
                pwp._id AS work_package_id,
                pwp._updated AS completion_time,
                pwp.quantity,
                ceil(EXTRACT(epoch FROM pwp._updated - (( SELECT min(project.start_date) AS min
                       FROM {config.RFX_CLIENT_SCHEMA}.project
                      WHERE project.organization_id = p.organization_id AND project.start_date IS NOT NULL))) / (7 * 24 * 60 * 60)::numeric)::integer AS relative_week,
                ( SELECT COALESCE(sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric), 0::numeric) AS "coalesce"
                       FROM {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi
                         JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id
                      WHERE pwpwi.project_work_package_id = pwp._id AND pwi.type::text = 'ARCHITECTURE'::text AND pwpwi._deleted IS NULL AND pwi._deleted IS NULL) AS ar_credits,
                ( SELECT COALESCE(sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric), 0::numeric) AS "coalesce"
                       FROM {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi
                         JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id
                      WHERE pwpwi.project_work_package_id = pwp._id AND pwi.type::text = 'DEVELOPMENT'::text AND pwpwi._deleted IS NULL AND pwi._deleted IS NULL) AS de_credits,
                ( SELECT COALESCE(sum(pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric), 0::numeric) AS "coalesce"
                       FROM {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi
                         JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id
                      WHERE pwpwi.project_work_package_id = pwp._id AND pwi.type::text = 'OPERATION'::text AND pwpwi._deleted IS NULL AND pwi._deleted IS NULL) AS op_credits
               FROM {config.RFX_CLIENT_SCHEMA}.project_work_package pwp
                 JOIN {config.RFX_CLIENT_SCHEMA}.project p ON pwp.project_id = p._id
              WHERE pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum AND pwp._deleted IS NULL AND p._deleted IS NULL AND pwp._updated IS NOT NULL
            )
     SELECT md5(done_work_packages.organization_id::text || done_work_packages.relative_week::text)::uuid AS _id,
        now() AS _created,
        now() AS _updated,
        done_work_packages.organization_id AS _creator,
        done_work_packages.organization_id AS _updater,
        NULL::timestamp without time zone AS _deleted,
        NULL::text AS _etag,
        NULL::text AS _realm,
        done_work_packages.organization_id,
        done_work_packages.relative_week AS week_number,
        'Week '::text || done_work_packages.relative_week AS week_label,
        round(COALESCE(sum(done_work_packages.ar_credits + done_work_packages.de_credits + done_work_packages.op_credits), 0::numeric), 2) AS total_credits,
        round(COALESCE(sum(done_work_packages.ar_credits), 0::numeric), 2) AS ar_credits,
        round(COALESCE(sum(done_work_packages.de_credits), 0::numeric), 2) AS de_credits,
        round(COALESCE(sum(done_work_packages.op_credits), 0::numeric), 2) AS op_credits,
        count(done_work_packages.work_package_id)::integer AS work_packages_completed
       FROM done_work_packages
      WHERE done_work_packages.relative_week > 0
      GROUP BY done_work_packages.organization_id, done_work_packages.relative_week
      ORDER BY done_work_packages.organization_id, done_work_packages.relative_week;
    """,
)


# ============================================================================
# STATUS VIEW
# ============================================================================

status_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_status",
    definition=f"""
    SELECT sk._id,
        sk._created,
        sk._updated,
        sk._creator,
        sk._updater,
        sk._deleted,
        sk._etag,
        sk._realm,
        s.entity_type,
        sk.status_id,
        sk.key,
        sk.name,
        sk.description,
        sk.is_initial,
        sk.is_final
       FROM {config.RFX_CLIENT_SCHEMA}.status s
         JOIN {config.RFX_CLIENT_SCHEMA}.status_key sk ON sk.status_id = s._id
      WHERE s.is_active = true AND sk._deleted IS NULL AND s._deleted IS NULL;
    """,
)


# ============================================================================
# REGISTER ALL VIEWS
# ============================================================================


def register_pg_entities(allow):
    """Register all PostgreSQL views for Alembic migrations"""
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info("REGISTER_PG_ENTITIES is disabled or not set.")
        return

    register_entities(
        [
            # Comment views
            comment_view,
            comment_attachment_view,
            comment_reaction_view,
            comment_reaction_summary_view,
            # Credit views
            credit_summary_view,
            credit_usage_view,
            # Project views
            project_view,
            project_credit_summary_view,
            project_document_view,
            # Work package views
            work_package_view,
            project_work_package_view,
            work_package_credit_usage_view,
            # Work item views
            work_item_view,
            work_item_listing_view,
            project_work_item_view,
            project_work_item_listing_view,
            # Ticket views
            inquiry_view,
            ticket_view,
            # Organization views
            organization_credit_summary_view,
            organization_weekly_credit_usage_view,
            # Status view
            status_view,
        ]
    )


# Auto-register if environment variable is set
register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
