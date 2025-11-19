"""
Work Item-related database views
"""

from alembic_utils.pg_view import PGView
from rfx_base import config

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
