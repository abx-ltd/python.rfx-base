from fluvius.data import DataAccessManager, item_query, list_query, value_query
from rfx_schema.rfx_client import RFXClientConnector, _schema  # noqa
from .policy import RFXClientPolicy  # noqa
from pypika import Table, Schema
from . import config

user_s = Schema(config.RFX_USER_SCHEMA)
client_s = Schema(config.RFX_CLIENT_SCHEMA)
message_s = Schema(config.RFX_MESSAGE_SCHEMA)
discussion_s = Schema(config.RFX_DISCUSS_SCHEMA)


user_profile = Table("profile", schema=user_s)
message_table = Table("message", schema=message_s)

credit_usage_table = Table("_credit_usage", schema=client_s)
work_package_table = Table("work_package", schema=client_s)
project_integration_table = Table("project_integration", schema=client_s)
project_ticket_table = Table("project_ticket", schema=client_s)

ticket_table = Table("ticket", schema=discussion_s)
status_table = Table("status", schema=discussion_s)
status_key_table = Table("status_key", schema=discussion_s)
status_transition_table = Table("status_transition", schema=discussion_s)


class RFXClientStateManager(DataAccessManager):
    __connector__ = RFXClientConnector
    __automodel__ = True

    @item_query
    def get_profile(self, profile_id):
        return (
            """
            select * from {user_profile}
            where _id = $1
        """.format(user_profile=user_profile),
            str(profile_id),
        )

    @list_query
    def get_profiles(self, profile_ids):
        if not profile_ids:
            return "SELECT * FROM {user_profile} WHERE 1=0".format(user_profile=user_profile), ()

        placeholders = ", ".join(f"${i + 1}" for i in range(len(profile_ids)))
        query = """
            select * from {user_profile}
            where _id in ({placeholders})
        """.format(user_profile=user_profile, placeholders=placeholders)
        return query, *[str(profile_id) for profile_id in profile_ids]

    @list_query
    def get_credit_usage_query(
        self,
        organization_id,
    ):
        query = """
            WITH date_series AS (
                SELECT 
                    (DATE_TRUNC('week', NOW()) - (i * INTERVAL '1 week'))::date AS week_date
                FROM generate_series(4, 0, -1) AS s(i)
            ),
            combined_data AS (
                SELECT
                    ds.week_date,
                    COALESCE(SUM(cu.ar_credits), 0) AS ar_credits,
                    COALESCE(SUM(cu.de_credits), 0) AS de_credits,
                    COALESCE(SUM(cu.op_credits), 0) AS op_credits,
                    COALESCE(SUM(cu.total_credits), 0) AS total_credits
                FROM date_series ds
                LEFT JOIN {credit_usage} cu
                    ON cu.organization_id = $1
                AND cu.usage_year = EXTRACT(isoyear FROM ds.week_date)
                AND cu.usage_week = EXTRACT(week FROM ds.week_date)
                GROUP BY ds.week_date
            ),
            fill_segments AS (
                SELECT
                    *,
                    COUNT(NULLIF(ar_credits,0)) OVER (ORDER BY week_date) AS ar_segment,
                    COUNT(NULLIF(de_credits,0)) OVER (ORDER BY week_date) AS de_segment,
                    COUNT(NULLIF(op_credits,0)) OVER (ORDER BY week_date) AS op_segment,
                    COUNT(NULLIF(total_credits,0)) OVER (ORDER BY week_date) AS total_segment
                FROM combined_data
            ),
            filled_data AS (
                SELECT
                    week_date,
                    FIRST_VALUE(ar_credits) OVER (PARTITION BY ar_segment ORDER BY week_date) AS ar_credits,
                    FIRST_VALUE(de_credits) OVER (PARTITION BY de_segment ORDER BY week_date) AS de_credits,
                    FIRST_VALUE(op_credits) OVER (PARTITION BY op_segment ORDER BY week_date) AS op_credits,
                    FIRST_VALUE(total_credits) OVER (PARTITION BY total_segment ORDER BY week_date) AS total_credits
                FROM fill_segments
            )
            SELECT
                ROW_NUMBER() OVER (ORDER BY week_date ASC) AS week_order,
                ar_credits,
                de_credits,
                op_credits,
                total_credits
            FROM filled_data
            ORDER BY week_order;
        """
        return query.format(credit_usage=credit_usage_table), str(organization_id)

    @item_query
    def count_work_packages(self, organization_id):
        return (
            """
            select COUNT(*) from {wp_table}
            where organization_id = $1
        """.format(wp_table=work_package_table),
            str(organization_id),
        )

    @item_query
    def count_messages(self, organization_id):
        return (
            """
            select COUNT(*) from {message_table}
            where organization_id = $1
        """.format(message_table=message_table),
            str(organization_id),
        )

    @item_query
    def count_open_inquiries(self, organization_id):
        return (
            """
            select COUNT(*) from {ticket_table}
            where organization_id = $1
            and status = 'OPEN'
        """.format(ticket_table=ticket_table),
            str(organization_id),
        )

    @value_query
    def get_status_id(self, entity_type):
        return (
            """
            select _id from {status_table}
            where entity_type = $1
            and _deleted is null
        """.format(status_table=status_table),
            str(entity_type),
        )

    @value_query
    def has_status_key(self, status_id, key):
        return (
            """
            select exists (
            select _id from {sk_table}
                where status_id = $1
                and key = $2
                and _deleted is null
            )
        """.format(sk_table=status_key_table),
            str(status_id),
            str(key),
        )

    @value_query
    def has_status_transition(self, status_id, current_status, new_status):
        query = """
            select exists (
                select 1
                from {st_table} st
                join {sk_table} ws_src on ws_src._id = st.src_status_key_id
                join {sk_table} ws_dst on ws_dst._id = st.dst_status_key_id
                where st.status_id = $1
                and ws_src.key = $2
                and ws_dst.key = $3
            )
        """
        return (
            query.format(st_table=status_transition_table, sk_table=status_key_table),
            str(status_id),
            str(current_status),
            str(new_status),
        )

    @item_query
    def get_project_integration(self, provider: str, external_id: str, project_id):
        """
        Tìm một bản ghi project-integration cụ thể dựa trên
        provider, external_id, và project_id.
        """

        query = """
            SELECT * FROM {pi_table}
            WHERE
                provider = $1 AND
                external_id = $2 AND
                project_id = $3
        """
        return query.format(pi_table=project_integration_table), provider, external_id, str(project_id)

    # Ticket Queries
    @value_query
    def get_project_id_by_ticket_id(self, ticket_id):
        """
        Lấy project_id từ bảng project-ticket bằng ticket_id.
        """
        return (
            """
            SELECT project_id FROM {pt_table}
            WHERE ticket_id = $1
        """.format(pt_table=project_ticket_table),
            str(ticket_id),
        )

    @list_query
    def get_ticket_ids_by_project_id(self, project_id):
        """
        Lấy danh sách ticket_id từ bảng project-ticket (schema cpo-client).
        """
        return (
            """
            SELECT ticket_id FROM {pt_table}
            WHERE project_id = $1
        """.format(pt_table=project_ticket_table),
            str(project_id),
        )

    @list_query
    def get_tickets_by_ids(self, ticket_ids: list):
        """
        Lấy thông tin chi tiết của các ticket dựa trên danh sách ID.
        """
        return (
            """
            SELECT * FROM {ticket_table}
            WHERE _id = ANY($1)
        """.format(ticket_table=ticket_table),
            ticket_ids,
        )
