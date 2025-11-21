"""
Credit-related database views
"""

from alembic_utils.pg_view import PGView
from rfx_base import config

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

organization_credit_summary_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_organization_credit_summary",
    definition=f"""
    WITH project_credit_calc AS (
            SELECT p.organization_id,
                sum((EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric) AS total_allocated,
                sum(
                    CASE
                        WHEN pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN (EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS total_used,
                sum(
                    CASE
                        WHEN pwi.type::text = 'ARCHITECTURE'::text THEN (EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS ar_allocated,
                sum(
                    CASE
                        WHEN pwi.type::text = 'ARCHITECTURE'::text AND pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN (EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS ar_used,
                sum(
                    CASE
                        WHEN pwi.type::text = 'DEVELOPMENT'::text THEN (EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS de_allocated,
                sum(
                    CASE
                        WHEN pwi.type::text = 'DEVELOPMENT'::text AND pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN (EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS de_used,
                sum(
                    CASE
                        WHEN pwi.type::text = 'OPERATION'::text THEN (EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
                        ELSE 0::numeric
                    END) AS op_allocated,
                sum(
                    CASE
                        WHEN pwi.type::text = 'OPERATION'::text AND pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN (EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric
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
    WITH calculated_items AS (
            SELECT p.organization_id,
                pwp._id AS work_package_id,
                pwp.date_complete,
                pwi.type,
                (EXTRACT(day FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric + EXTRACT(hour FROM COALESCE(pwi.estimate, '00:00:00'::interval)) + EXTRACT(minute FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0) * pwi.credit_per_unit * COALESCE(pwp.quantity, 1)::numeric AS credit_amount
            FROM {config.RFX_CLIENT_SCHEMA}.project_work_package pwp
                JOIN {config.RFX_CLIENT_SCHEMA}.project p ON pwp.project_id = p._id
                JOIN {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi ON pwp._id = pwpwi.project_work_package_id
                JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id
            WHERE pwp.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum AND pwp.date_complete IS NOT NULL AND pwp._deleted IS NULL AND p._deleted IS NULL AND pwpwi._deleted IS NULL AND pwi._deleted IS NULL
            )
    SELECT md5(ci.organization_id::text || date_trunc('week'::text, ci.date_complete)::text)::uuid AS _id,
        now() AS _created,
        now() AS _updated,
        ci.organization_id AS _creator,
        ci.organization_id AS _updater,
        NULL::timestamp without time zone AS _deleted,
        NULL::text AS _etag,
        NULL::text AS _realm,
        ci.organization_id,
        date_part('week'::text, date_trunc('week'::text, ci.date_complete))::integer AS week_number,
        to_char(date_trunc('week'::text, ci.date_complete), 'IYYY-"W"IW'::text) AS week_label,
        date_trunc('week'::text, ci.date_complete)::date AS week_start_date,
        round(COALESCE(sum(ci.credit_amount), 0::numeric), 2) AS total_credits,
        round(COALESCE(sum(
            CASE
                WHEN ci.type::text = 'ARCHITECTURE'::text THEN ci.credit_amount
                ELSE 0::numeric
            END), 0::numeric), 2) AS ar_credits,
        round(COALESCE(sum(
            CASE
                WHEN ci.type::text = 'DEVELOPMENT'::text THEN ci.credit_amount
                ELSE 0::numeric
            END), 0::numeric), 2) AS de_credits,
        round(COALESCE(sum(
            CASE
                WHEN ci.type::text = 'OPERATION'::text THEN ci.credit_amount
                ELSE 0::numeric
            END), 0::numeric), 2) AS op_credits,
        count(DISTINCT ci.work_package_id)::integer AS work_packages_completed
    FROM calculated_items ci
    GROUP BY ci.organization_id, (date_trunc('week'::text, ci.date_complete))
    ORDER BY ci.organization_id, (date_trunc('week'::text, ci.date_complete)::date) DESC;
    """,
)


credit_purchase_history_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_credit_purchase_history",
    definition=f"""
    SELECT cp._id,
        cp._created,
        cp._updated,
        cp._creator,
        cp._updater,
        cp._deleted,
        cp._etag,
        cp._realm,
        cp._id AS purchase_id,
        cp.organization_id,
        cp.purchase_date,
        round(cp.ar_credits::numeric, 2) AS ar_credits,
        round(cp.de_credits::numeric, 2) AS de_credits,
        round(cp.op_credits::numeric, 2) AS op_credits,
        round(cp.total_credits::numeric, 2) AS total_credits,
        round(cp.amount::numeric, 2) AS amount,
        cp.currency,
        cp.payment_method,
        cp.transaction_id,
        cp.invoice_number,
        cp.discount_code,
        round(COALESCE(cp.discount_amount, 0::numeric), 2) AS discount_amount,
        round(cp.amount - COALESCE(cp.discount_amount, 0::numeric), 2) AS final_amount,
        cp.status,
        pkg.package_name,
        pkg.package_code,
        cp.purchased_by,
        prof.name__given AS purchaser_name,
        prof.telecom__email AS purchaser_email,
        cp._created AS created_at,
        cp.completed_date
    FROM {config.RFX_CLIENT_SCHEMA}.credit_purchase cp
        LEFT JOIN {config.RFX_CLIENT_SCHEMA}.credit_package pkg ON cp.package_id = pkg._id
        LEFT JOIN {config.RFX_USER_SCHEMA}.profile prof ON cp.purchased_by = prof._id
    WHERE cp._deleted IS NULL
    ORDER BY cp.organization_id, cp.purchase_date DESC;
    """,
)

credit_usage_summary_view = PGView(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="_credit_usage_summary",
    definition=f"""
    WITH usage_summary AS (
         SELECT EXTRACT(year FROM credit_usage_log.usage_date)::integer AS usage_year,
            EXTRACT(month FROM credit_usage_log.usage_date)::integer AS usage_month,
            EXTRACT(week FROM credit_usage_log.usage_date)::integer AS usage_week,
            date_trunc('week'::text, credit_usage_log.usage_date) AS week_start_date,
            round(sum(
                CASE
                    WHEN credit_usage_log.work_type::text = 'ARCHITECTURE'::text THEN credit_usage_log.credits_used
                    ELSE 0::numeric
                END), 2) AS ar_credits,
            round(sum(
                CASE
                    WHEN credit_usage_log.work_type::text = 'DEVELOPMENT'::text THEN credit_usage_log.credits_used
                    ELSE 0::numeric
                END), 2) AS de_credits,
            round(sum(
                CASE
                    WHEN credit_usage_log.work_type::text = 'OPERATION'::text THEN credit_usage_log.credits_used
                    ELSE 0::numeric
                END), 2) AS op_credits,
            round(sum(credit_usage_log.credits_used), 2) AS total_credits,
            min(credit_usage_log._created) AS first_created,
            max(credit_usage_log._updated) AS last_updated
           FROM {config.RFX_CLIENT_SCHEMA}.credit_usage_log
          WHERE credit_usage_log._deleted IS NULL
          GROUP BY (EXTRACT(year FROM credit_usage_log.usage_date)), (EXTRACT(month FROM credit_usage_log.usage_date)), (EXTRACT(week FROM credit_usage_log.usage_date)), (date_trunc('week'::text, credit_usage_log.usage_date))
        )
 SELECT uuid_generate_v4() AS _id,
    usage_summary.first_created AS _created,
    usage_summary.last_updated AS _updated,
    NULL::uuid AS _creator,
    NULL::uuid AS _updater,
    NULL::timestamp with time zone AS _deleted,
    gen_random_uuid()::character varying AS _etag,
    NULL::character varying AS _realm,
    usage_summary.usage_year,
    usage_summary.usage_month,
    usage_summary.usage_week,
    usage_summary.week_start_date,
    usage_summary.ar_credits,
    usage_summary.de_credits,
    usage_summary.op_credits,
    usage_summary.total_credits
   FROM usage_summary
  ORDER BY usage_summary.usage_year DESC, usage_summary.usage_month DESC, usage_summary.usage_week DESC;
    """,
)
