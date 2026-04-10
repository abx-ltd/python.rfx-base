from rfx_base import config
from alembic_utils.pg_view import PGView

mailbox_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_mailbox",
    definition=f"""
    SELECT
        mb._id,
        mb._created,
        mb._updated,
        mb._deleted,

        mb.name AS mailbox_name,
        mb.profile_id AS mailbox_profile_id,
        mb.telecom_phone,
        mb.telecom_email,
        mb.description,
        mb.url,
        mb.mailbox_type,

        -- members
        (
            SELECT COALESCE(
                array_agg(mmbr.member_id),
                ARRAY[]::uuid[]
            )
            FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox_member mmbr
            WHERE mmbr.mailbox_id = mb._id
            AND mmbr._deleted IS NULL
        ) AS member_ids

    FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb
    WHERE mb._deleted IS NULL;
    """,
)