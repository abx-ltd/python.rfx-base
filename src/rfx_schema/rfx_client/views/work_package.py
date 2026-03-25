from .. import SCHEMA
from alembic_utils.pg_view import PGView
from alembic_utils.pg_function import PGFunction
fn_get_resource_json = PGFunction(
    schema=SCHEMA,
    signature="fn_get_resource_json(schema_name text, table_name text, row_id uuid)",
    definition="""
    RETURNS jsonb
    LANGUAGE plpgsql
    STABLE
    AS $function$
    DECLARE
        result jsonb;
        sql_query text;
    BEGIN
        IF schema_name IS NULL OR table_name IS NULL OR row_id IS NULL THEN
            RETURN NULL;
        END IF;

        sql_query := format(
            'SELECT to_jsonb(t) FROM %I.%I t WHERE t._id = $1 AND t._deleted IS NULL',
            schema_name,
            table_name
        );

        EXECUTE sql_query INTO result USING row_id;
        RETURN result;
    EXCEPTION
        WHEN undefined_table OR undefined_column THEN
            RETURN NULL;
        WHEN others THEN
            RETURN NULL;
    END;
    $function$
    """,
)

work_package_view = PGView(
    schema=SCHEMA,
    signature="_work_package",
    definition=f"""
    WITH work_items AS (
            SELECT link.work_package_id,
                wi_1._id AS work_item_id,
                wi_1.type,
                (EXTRACT(day FROM COALESCE(wi_1.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(wi_1.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(wi_1.estimate, '00:00:00'::interval)) / 60.0) * COALESCE(wi_1.credit_per_unit, 0::numeric) AS calculated_credits,
                rt.alias AS type_alias
            FROM {SCHEMA}.work_package_work_item link
                JOIN {SCHEMA}.work_item wi_1 ON wi_1._id = link.work_item_id AND wi_1._deleted IS NULL
                LEFT JOIN {SCHEMA}.ref__work_item_type rt ON wi_1.type::text = rt.key::text
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
        wp.category,
        wp.example_description,
        wp.complexity_level,
        wp.estimate,
        wp.organization_id IS NOT NULL AS is_custom,
        array_agg(DISTINCT wi.type_alias)::character varying(50)[] AS type_list,
        count(DISTINCT wi.work_item_id) AS work_item_count,
        CASE
            WHEN wp.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp.total_credits, 0::numeric), 2)
            ELSE round(COALESCE(sum(wi.calculated_credits), 0::numeric), 2)
        END AS credits,
        CASE
            WHEN wp.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp.total_ar_credits, 0::numeric), 2)
            ELSE round(COALESCE(sum(wi.calculated_credits) FILTER (WHERE wi.type::text = 'ARCHITECTURE'::text), 0::numeric), 2)
        END AS architectural_credits,
        CASE
            WHEN wp.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp.total_de_credits, 0::numeric), 2)
            ELSE round(COALESCE(sum(wi.calculated_credits) FILTER (WHERE wi.type::text = 'DEVELOPMENT'::text), 0::numeric), 2)
        END AS development_credits,
        CASE
            WHEN wp.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp.total_op_credits, 0::numeric), 2)
            ELSE round(COALESCE(sum(wi.calculated_credits) FILTER (WHERE wi.type::text = 'OPERATION'::text), 0::numeric), 2)
        END AS operation_credits,
        CASE
            WHEN wp.method_calculated = 'WORKPACKAGE' THEN round((COALESCE(wp.total_ar_credits, 0::numeric) + COALESCE(wp.total_de_credits, 0::numeric)) * 30.0, 2)
            ELSE round(COALESCE(sum(wi.calculated_credits) FILTER (WHERE wi.type::text = ANY (ARRAY['ARCHITECTURE'::text, 'DEVELOPMENT'::text])), 0::numeric) * 30.0, 2)
        END AS upfront_cost,
        CASE
            WHEN wp.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp.total_op_credits, 0::numeric) * 30.0, 2)
            ELSE round(COALESCE(sum(wi.calculated_credits) FILTER (WHERE wi.type::text = 'OPERATION'::text), 0::numeric) * 30.0, 2)
        END AS monthly_cost
    FROM {SCHEMA}.work_package wp
        LEFT JOIN work_items wi ON wi.work_package_id = wp._id
    WHERE wp._deleted IS NULL
    GROUP BY wp._id, wp._created, wp._updated, wp._creator, wp._updater, wp._deleted, wp._etag, wp._realm, wp.organization_id, wp.work_package_name, wp.description, wp.example_description, wp.complexity_level, wp.estimate, wp.method_calculated, wp.total_credits, wp.total_ar_credits, wp.total_de_credits, wp.total_op_credits;
    """,
)

project_work_package_view = PGView(
    schema=SCHEMA,
    signature="_project_work_package",
    definition=f"""
    WITH work_items AS (
            SELECT link.project_work_package_id,
                wi_1._id AS project_work_item_id,
                wi_1.type,
                (EXTRACT(day FROM COALESCE(wi_1.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(wi_1.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(wi_1.estimate, '00:00:00'::interval)) / 60.0) * COALESCE(wi_1.credit_per_unit, 0::numeric) AS calculated_credits
            FROM {SCHEMA}.project_work_package_work_item link
                JOIN {SCHEMA}.project_work_item wi_1 ON wi_1._id = link.project_work_item_id AND wi_1._deleted IS NULL
            WHERE link._deleted IS NULL
            ), deliverable_counts AS (
            SELECT d.project_work_item_id,
                count(DISTINCT d._id) AS deliverable_count
            FROM {SCHEMA}.project_work_item_deliverable d
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
        pwp.params,
        array_agg(DISTINCT rwt.alias)::character varying(50)[] AS type_list,
        count(DISTINCT wi.project_work_item_id) AS work_item_count,
        CASE
            WHEN wp_base.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp_base.total_credits, 0::numeric) * COALESCE(pwp.quantity, 1)::numeric, 2)
            ELSE round(COALESCE(sum(wi.calculated_credits), 0::numeric) * COALESCE(pwp.quantity, 1)::numeric, 2)
        END AS credits,
        CASE
            WHEN wp_base.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp_base.total_ar_credits, 0::numeric) * COALESCE(pwp.quantity, 1)::numeric, 2)
            ELSE round(COALESCE(sum(wi.calculated_credits) FILTER (WHERE upper(wi.type::text) = 'ARCHITECTURE'::text), 0::numeric) * COALESCE(pwp.quantity, 1)::numeric, 2)
        END AS architectural_credits,
        CASE
            WHEN wp_base.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp_base.total_de_credits, 0::numeric) * COALESCE(pwp.quantity, 1)::numeric, 2)
            ELSE round(COALESCE(sum(wi.calculated_credits) FILTER (WHERE upper(wi.type::text) = 'DEVELOPMENT'::text), 0::numeric) * COALESCE(pwp.quantity, 1)::numeric, 2)
        END AS development_credits,
        CASE
            WHEN wp_base.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp_base.total_op_credits, 0::numeric) * COALESCE(pwp.quantity, 1)::numeric, 2)
            ELSE round(COALESCE(sum(wi.calculated_credits) FILTER (WHERE upper(wi.type::text) = 'OPERATION'::text), 0::numeric) * COALESCE(pwp.quantity, 1)::numeric, 2)
        END AS operation_credits,
        CASE
            WHEN wp_base.method_calculated = 'WORKPACKAGE' THEN round((COALESCE(wp_base.total_ar_credits, 0::numeric) + COALESCE(wp_base.total_de_credits, 0::numeric)) * COALESCE(pwp.quantity, 1)::numeric * 100.0, 2)
            ELSE round(COALESCE(sum(wi.calculated_credits), 0::numeric) * COALESCE(pwp.quantity, 1)::numeric * 100.0, 2)
        END AS upfront_cost,
        CASE
            WHEN wp_base.method_calculated = 'WORKPACKAGE' THEN round(COALESCE(wp_base.total_op_credits, 0::numeric) * COALESCE(pwp.quantity, 1)::numeric * 100.0, 2)
            ELSE 0::numeric
        END AS monthly_cost,
        COALESCE(sum(dc.deliverable_count), 0::numeric) AS total_deliverables,
        pwp.status AS status_wp
    FROM {SCHEMA}.project_work_package pwp
        JOIN {SCHEMA}.project p ON p._id = pwp.project_id
        LEFT JOIN {SCHEMA}.work_package wp_base ON wp_base._id = pwp.work_package_id AND wp_base._deleted IS NULL
        LEFT JOIN work_items wi ON wi.project_work_package_id = pwp._id
        LEFT JOIN {SCHEMA}.project_work_item pwi_join ON wi.project_work_item_id = pwi_join._id
        LEFT JOIN {SCHEMA}.ref__work_item_type rwt ON pwi_join.type::text = rwt.key::text
        LEFT JOIN deliverable_counts dc ON dc.project_work_item_id = wi.project_work_item_id
    WHERE pwp._deleted IS NULL
    GROUP BY pwp._id, pwp.project_id, pwp.work_package_id, pwp.quantity, pwp.work_package_name, pwp.work_package_is_custom, pwp.work_package_estimate, p.status, wp_base.method_calculated, wp_base.total_credits, wp_base.total_ar_credits, wp_base.total_de_credits, wp_base.total_op_credits;
    """,
)

project_work_package_relationship_view = PGView(
    schema=SCHEMA,
    signature="_project_work_package_relationship",
    definition=f"""
    SELECT pwpr._id,
        pwpr._created,
        pwpr._updated,
        pwpr._creator,
        pwpr._updater,
        pwpr._deleted,
        pwpr._etag,
        pwpr._realm,
        pwpr.project_work_package_id,
        pwpr.schema_relation,
        pwpr.resource_name,
        pwpr.resource_id,
        pwp.project_id,
        pwp.work_package_id,
        pwp.quantity,
        pwp.status AS project_work_package_status,
        pwp.work_package_name AS project_work_package_name,
        p.name AS project_name,
        wp.work_package_name AS work_package_name,
        res.resource_data
    FROM {SCHEMA}.project_work_package_relationship pwpr
        JOIN {SCHEMA}.project_work_package pwp ON pwp._id = pwpr.project_work_package_id AND pwp._deleted IS NULL
        LEFT JOIN {SCHEMA}.project p ON p._id = pwp.project_id AND p._deleted IS NULL
        LEFT JOIN {SCHEMA}.work_package wp ON wp._id = pwp.work_package_id AND wp._deleted IS NULL
        LEFT JOIN LATERAL (
            SELECT {SCHEMA}.fn_get_resource_json(
                COALESCE(NULLIF(trim(pwpr.schema_relation), ''), '{SCHEMA}'),
                pwpr.resource_name,
                pwpr.resource_id
            ) AS resource_data
        ) res ON TRUE
    WHERE pwpr._deleted IS NULL;
    """,
)

work_package_credit_usage_view = PGView(
    schema=SCHEMA,
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
           FROM {SCHEMA}.credit_usage_log cul
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
           FROM {SCHEMA}.project_work_package pwp
             LEFT JOIN {SCHEMA}._project_work_package vwp ON pwp.work_package_id = vwp.work_package_id AND pwp.project_id = vwp.project_id
          WHERE pwp._deleted IS NULL
        ), wi_stats AS (
         SELECT pwp.work_package_id,
            pwp.project_id,
            count(DISTINCT pwi.project_work_item_id)::integer AS completed_work_items
           FROM {SCHEMA}.project_work_package pwp
             JOIN {SCHEMA}.project_work_package_work_item pwi ON pwp._id = pwi.project_work_package_id
             JOIN {SCHEMA}.project_work_item item ON pwi.project_work_item_id = item._id
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
         LEFT JOIN {SCHEMA}.project p ON wpi.project_id = p._id
      ORDER BY wpi.project_id, wpi.work_package_name;
    """,
)
