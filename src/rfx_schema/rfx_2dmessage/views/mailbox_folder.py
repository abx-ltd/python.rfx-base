from rfx_base import config
from alembic_utils.pg_view import PGView

mailbox_folder_view = PGView(
    schema=config.RFX_2DMESSAGE_SCHEMA,
    signature="_mailbox_folder",
    definition=f"""
    SELECT
            mb._id,                
            mb._id AS mailbox_id,
            mb.name AS mailbox_name,

            mm.assigned_to_profile_id,

            -- =========================
            -- COUNTS
            -- =========================
            COUNT(*) FILTER (WHERE mm.folder = 'inbox') AS inbox_count,
            COUNT(*) FILTER (WHERE mm.folder = 'trash') AS trashed_count,
            COUNT(*) FILTER (WHERE mm.folder = 'archived') AS archived_count,

            -- optional tổng
            COUNT(*) AS total_count,

            mb._created,
            mb._updated,
            mb._deleted,
            mb._realm,
            mb._creator,
            mb._updater,
            mb._etag
            

        FROM cpo_2dmessage.mailbox mb

        LEFT JOIN cpo_2dmessage.message_mailbox_state mm
            ON mm.mailbox_id = mb._id
        AND mm._deleted IS NULL

        WHERE mb._deleted IS NULL

        GROUP BY
            mb._id,
            mb.name,
            mm.assigned_to_profile_id;
    """
)