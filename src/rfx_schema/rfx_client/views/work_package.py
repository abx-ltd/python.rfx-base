"""
Work Package-related database views
"""

from alembic_utils.pg_view import PGView
from rfx_base import config

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
    definition="""
    WITH work_items AS (
            SELECT link.project_work_package_id,
                wi_1._id AS project_work_item_id,
                wi_1.type,
                wi_1.price_unit,
                wi_1.credit_per_unit,
                wi_1.price_unit * wi_1.credit_per_unit AS total_credits,
                wi_1.price_unit * wi_1.credit_per_unit * 30.0 AS total_cost
            FROM cpo_client.project_work_package_work_item link
                JOIN cpo_client.project_work_item wi_1 ON wi_1._id = link.project_work_item_id AND wi_1._deleted IS NULL
            WHERE link._deleted IS NULL
            ), deliverable_counts AS (
            SELECT d.project_work_item_id,
                count(DISTINCT d._id) AS deliverable_count
            FROM cpo_client.project_work_item_deliverable d
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
        COALESCE(sum(dc.deliverable_count), 0::numeric) AS total_deliverables,
        pwp.status AS status_wp
    FROM cpo_client.project_work_package pwp
        JOIN cpo_client.project p ON p._id = pwp.project_id
        LEFT JOIN work_items wi ON wi.project_work_package_id = pwp._id
        LEFT JOIN cpo_client.ref__work_item_type rwt ON wi.type::text = rwt.key::text
        LEFT JOIN deliverable_counts dc ON dc.project_work_item_id = wi.project_work_item_id
    WHERE pwp._deleted IS NULL
    GROUP BY pwp._id, pwp.project_id, pwp.work_package_id, pwp.quantity, pwp.work_package_name, pwp.work_package_is_custom, pwp.work_package_estimate, p.status;
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
