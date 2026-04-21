from rfx_base import config
from alembic_utils.pg_view import PGView

mailbox_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_mailbox",
    definition=f"""
    SELECT
        -- =========================
        -- METADATA
        -- =========================
        mb._id,
        mb._id AS mailbox_id,

        -- =========================
        -- MAILBOX INFO
        -- =========================
        mb.name AS mailbox_name,
        mb.profile_id AS mailbox_profile_id,
        mb.telecom_phone,
        mb.telecom_email,
        mb.description,
        mb.url,
        mb.mailbox_type,

        -- =========================
        -- MEMBER (SCALAR - FILTER)
        -- =========================
        mmbr.member_id,

        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'id', m2.member_id,
                        'name__given', p.name__given,
                        'name__family', p.name__family,
                        'email', p.telecom__email,
                        'role', m2.role
                    )
                    ORDER BY p.name__given
                )
                FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox_member m2
                JOIN {config.RFX_USER_SCHEMA}.profile p
                    ON p._id = m2.member_id
                    AND p._deleted IS NULL
                WHERE m2.mailbox_id = mb._id
                    AND m2._deleted IS NULL
            ),
            '[]'::jsonb
        ) AS members_info,

        -- =========================
        -- MEMBERS (JSON)
        -- =========================
        COALESCE(
            (
                SELECT jsonb_agg(m2.member_id ORDER BY m2.member_id)
                FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox_member m2
                WHERE m2.mailbox_id = mb._id
                AND m2._deleted IS NULL
            ),
            '[]'::jsonb
        ) AS members,

        /*
        -- =========================
        -- CATEGORIES
        -- =========================
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'category_id', c._id,
                        'key', c.key,
                        'name', c.name
                    )
                    ORDER BY c.name
                )
                FROM {config.RFX_2DMESSAGE_SCHEMA}.category c
                WHERE c.mailbox_id = mb._id
                AND c._deleted IS NULL
            ),
            '[]'::jsonb
        ) AS categories,

        -- =========================
        -- TAGS
        -- =========================
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'tag_id', t._id,
                        'key', t.key,
                        'name', t.name,
                        'background_color', t.background_color,
                        'font_color', t.font_color
                    )
                    ORDER BY t.name
                )
                FROM {config.RFX_2DMESSAGE_SCHEMA}.tag t
                WHERE t.mailbox_id = mb._id
                AND t._deleted IS NULL
            ),
            '[]'::jsonb
        ) AS tags
        */

        mb._created,
        mb._updated,
        mb._deleted,
        mb._realm,
        mb._creator,
        mb._updater,
        mb._etag

    FROM {config.RFX_2DMESSAGE_SCHEMA}.mailbox mb

    -- JOIN để expose member_id
    JOIN {config.RFX_2DMESSAGE_SCHEMA}.mailbox_member mmbr
        ON mmbr.mailbox_id = mb._id
    AND mmbr._deleted IS NULL

    WHERE mb._deleted IS NULL;
    """
)