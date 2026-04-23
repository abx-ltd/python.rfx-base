from rfx_base import config
from alembic_utils.pg_view import PGView

mailbox_member_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_mailbox_member",
    definition=f"""
    SELECT
        -- =========================
        -- RELATION KEY
        -- =========================
        p._id,
        mm.mailbox_id,
        mm.member_id,

        -- =========================
        -- MAILBOX INFO
        -- =========================
        mb.name AS mailbox_name,
        mb.profile_id AS mailbox_profile_id,

        -- =========================
        -- MEMBER PROFILE
        -- =========================
        p.name__given,
        p.name__family,
        p.telecom__email,
        p.telecom__phone,

        -- =========================
        -- MEMBER ROLE
        -- =========================
        mm.role,

        -- =========================
        -- MEMBER METADATA
        -- =========================
        mm._created AS joined_at,
        mm._created,
        mm._updated,
        mm._deleted,
        mm._realm,
        mm._creator,
        mm._updater,
        mm._etag

    FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox_member mm

    JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb
        ON mb._id = mm.mailbox_id
        AND mb._deleted IS NULL

    JOIN {config.RFX_USER_SCHEMA}.profile p
        ON p._id = mm.member_id
        AND p._deleted IS NULL

    WHERE mm._deleted IS NULL;
    """
)