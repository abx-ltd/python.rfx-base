from rfx_base import config
from alembic_utils.pg_view import PGView

message_tag_view= PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_message_tag",
    definition=f"""
    SELECT
        -- =========================
        -- MESSAGE
        -- =========================
        m._id AS message_id,
        m.subject,
        m.content,
        m._created AS message_created_at,

        -- =========================
        -- CATEGORY (OPTIONAL)
        -- =========================
        m.category_id,
        cat.name AS category_name,
        cat.key AS category_key,

        -- =========================
        -- TAG
        -- =========================
        t._id AS tag_id,
        t.key AS tag_key,
        t.name AS tag_name,
        t.background_color,
        t.font_color,

        -- =========================
        -- MAILBOX (FROM TAG)
        -- =========================
        mb._id AS mailbox_id,
        mb.name AS mailbox_name,

        -- =========================
        -- RELATION
        -- =========================
        mt._created,
        mt._updated,
        mt._deleted,
        mt._realm,
        mt._creator,
        mt._updater,
        mt._etag

    FROM {config.RFX_2DMESSAGE_SCHEMA}.message_tag mt

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.message m
        ON m._id = mt.message_id
    AND m._deleted IS NULL

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.tag t
        ON t._id = mt.tag_id
    AND t._deleted IS NULL

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb
        ON mb._id = t.mailbox_id
    AND mb._deleted IS NULL

    LEFT JOIN {config.RFX_2DMESSAGE_SCHEMA}.category cat
        ON cat._id = m.category_id
    AND cat._deleted IS NULL

    WHERE mt._deleted IS NULL;
    """
)