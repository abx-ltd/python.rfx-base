"""
Project-related database views
"""

from alembic_utils.pg_view import PGView
from rfx_base import config

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
        round(COALESCE(( SELECT sum((EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric) AS sum
            FROM {config.RFX_CLIENT_SCHEMA}.project_work_package pwp
                JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi ON pwp._id = pwpwi.project_work_package_id AND pwpwi._deleted IS NULL
                JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id AND pwi._deleted IS NULL
            WHERE pwp.project_id = p._id AND pwp._deleted IS NULL), 0::numeric), 2) AS total_credit,
        round(COALESCE(( SELECT sum((EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric) AS sum
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


project_estimate_summary_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_project_estimate_summary",
    definition="""
    WITH project_credits AS (
         SELECT pwp.project_id,
            sum(wi.price_unit * wi.credit_per_unit * pwp.quantity::numeric) FILTER (WHERE wi.type::text = 'ARCHITECTURE'::text) AS architectural_credits,
            sum(wi.price_unit * wi.credit_per_unit * pwp.quantity::numeric) FILTER (WHERE wi.type::text = 'DEVELOPMENT'::text) AS development_credits,
            sum(wi.price_unit * wi.credit_per_unit * pwp.quantity::numeric) FILTER (WHERE wi.type::text = 'OPERATION'::text) AS operation_credits,
            sum(wi.price_unit * wi.credit_per_unit * pwp.quantity::numeric) AS total_credits
           FROM cpo_client.project_work_package pwp
             JOIN cpo_client.work_package_work_item wpwi ON pwp.work_package_id = wpwi.work_package_id AND wpwi._deleted IS NULL
             JOIN cpo_client.work_item wi ON wpwi.work_item_id = wi._id AND wi._deleted IS NULL
          WHERE pwp._deleted IS NULL
          GROUP BY pwp.project_id
        ), referral AS (
         SELECT p_1._id AS project_id,
            COALESCE(pr.discount_value, 0::numeric) AS discount_value
           FROM cpo_client.project p_1
             LEFT JOIN cpo_client.promotion pr ON pr.code::text = p_1.referral_code_used::text AND pr._deleted IS NULL AND pr.valid_from <= now() AND pr.valid_until >= now() AND pr.current_uses < pr.max_uses
        )
        SELECT p._id,
            p._created,
            p._updated,
            p._creator,
            p._updater,
            p._deleted,
            p._etag,
            p._realm,
            p.organization_id,
            COALESCE(pc.architectural_credits, 0::numeric) AS architectural_credits,
            COALESCE(pc.development_credits, 0::numeric) AS development_credits,
            COALESCE(pc.operation_credits, 0::numeric) AS operation_credits,
            r.discount_value,
            r.discount_value / 30.0 AS free_credits,
            COALESCE(pc.total_credits, 0::numeric) AS total_credits_raw,
            COALESCE(pc.total_credits, 0::numeric) - r.discount_value / 30.0 AS total_credits_after_discount,
            (COALESCE(pc.total_credits, 0::numeric) - r.discount_value / 30.0) * 30.0 AS total_cost
        FROM cpo_client.project p
            LEFT JOIN project_credits pc ON pc.project_id = p._id
            LEFT JOIN referral r ON r.project_id = p._id;
    """,
)


document_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_document",
    definition="""
    SELECT d._id,
    d._created,
    d._updated,
    d._creator,
    d._updater,
    d._deleted,
    d._etag,
    d._realm,
    d.name AS document_name,
    d.description,
    d.doc_type,
    d.file_size,
    d.status,
    d.organization_id,
    d.media_entry_id,
    me.filename,
    me.filemime,
    me.fspath,
    me.cdn_url,
    me.length AS file_length,
    jsonb_build_object('id', creator._id, 'name', COALESCE(creator.preferred_name, concat(creator.name__given, ' ', creator.name__family)::character varying), 'avatar', creator.picture_id) AS created_by,
    COALESCE(( SELECT json_agg(jsonb_build_object('id', part._id, 'name', COALESCE(part.preferred_name, concat(part.name__given, ' ', part.name__family)::character varying), 'avatar', part.picture_id, 'role', dp.role)) AS json_agg
           FROM cpo_client.document_participant dp
             JOIN cpo_user.profile part ON part._id = dp.participant_id
          WHERE dp.document_id = d._id AND dp._deleted IS NULL), '[]'::json) AS participants,
    COALESCE(( SELECT count(DISTINCT dp.participant_id) AS count
           FROM cpo_client.document_participant dp
          WHERE dp.document_id = d._id AND dp._deleted IS NULL), 0::bigint)::integer AS participant_count,
    GREATEST(d._created, d._updated) AS activity
   FROM cpo_client.document d
     LEFT JOIN "cpo-media"."media-entry" me ON d.media_entry_id = me._id
     LEFT JOIN cpo_user.profile creator ON d._creator = creator._id
  WHERE d._deleted IS NULL
  ORDER BY d.organization_id, d._created DESC;
    """,
)
