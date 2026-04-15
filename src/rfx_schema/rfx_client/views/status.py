from .. import SCHEMA, domain_config


status_view = PGView(
    schema=SCHEMA,
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
       FROM {SCHEMA}.status s
         JOIN {SCHEMA}.status_key sk ON sk.status_id = s._id
      WHERE s.is_active = true AND sk._deleted IS NULL AND s._deleted IS NULL;
    """,
)
