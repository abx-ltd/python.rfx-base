from .. import SCHEMA, domain_config


supplier_service_view = PGView(
    schema=SCHEMA,
    signature="_supplier_service",
    definition=f"""
    SELECT
    ss._id,
    ss.status AS supplier_service_status,
    ss.description AS supplier_service_description,
    ss._created,
    ss._updated,
    ss._creator,
    ss._updater,
    ss._deleted,
    ss._etag,
    ss._realm,


    sup._id AS supplier_id,
    sup.code AS supplier_code,
    sup.supplier_name,
    sup.tax_code,
    sup.contact_email,
    sup.contact_phone,
    sup.status AS supplier_status,
    sc._id AS service_id,
    sc.code AS service_code,
    sc.service_name,
    sc.category AS service_category,
    sc.status AS service_category_status

FROM {SCHEMA}.supplier_service ss
JOIN {SCHEMA}.supplier sup ON ss.supplier_id = sup._id
JOIN {SCHEMA}.service_category sc ON ss.service_id = sc._id;
    """,
)
