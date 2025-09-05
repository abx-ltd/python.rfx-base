from fluvius.data import DataAccessManager, item_query, list_query, value_query
from .model import RFXClientConnector


class RFXClientStateManager(DataAccessManager):
    __connector__ = RFXClientConnector
    __automodel__ = True

    @item_query
    def get_profile(self, profile_id):
        return """
            select * from "cpo-user"."profile"
            where _id = $1
        """, str(profile_id)

    @list_query
    def get_profiles(self, profile_ids):
        if not profile_ids:
            return "SELECT * FROM \"cpo-user\".\"profile\" WHERE 1=0", ()

        placeholders = ', '.join(f'${i+1}' for i in range(len(profile_ids)))
        query = f"""
            select * from "cpo-user"."profile"
            where _id in ({placeholders})
        """
        return query, *[str(profile_id) for profile_id in profile_ids]

    @list_query
    def get_credit_usage_query(
        self,
        organization_id,
    ):
        return """
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
                LEFT JOIN "cpo-client"."_credit-usage" cu
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
        """, str(organization_id)

    @item_query
    def count_work_packages(self, organization_id):
        return """
            select COUNT(*) from "cpo-client"."work-package"
            where organization_id = $1
        """, str(organization_id)

    @item_query
    def count_messages(self, organization_id):
        return """
            select COUNT(*) from "cpo-message"."message"
            where organization_id = $1
        """, str(organization_id)\


    @item_query
    def count_open_inquiries(self, organization_id):
        return """
            select COUNT(*) from "cpo-discussion"."ticket"
            where organization_id = $1
            and status = 'OPEN'
        """, str(organization_id)

    @value_query
    def workflow_id(self, entity_type):
        return """
            select _id from "cpo-discussion"."workflow"
            where entity_type = $1
            and _deleted is null
        """, str(entity_type)

    @value_query
    def workflow_status_id(self, workflow_id, status):
        return """
            select _id from "cpo-discussion"."workflow-status"
            where workflow_id = $1
            and key = $2
            and _deleted is null
        """, str(workflow_id), str(status)

    @value_query
    def has_workflow_transition(self, workflow_id, current_status, new_status):
        return """
            select exists (
                select 1
                from "cpo-discussion"."workflow-transition" wt
                join "cpo-discussion"."workflow-status" ws_src on ws_src._id = wt.src_status_id
                join "cpo-discussion"."workflow-status" ws_dst on ws_dst._id = wt.dst_status_id
                where wt.workflow_id = $1
                and ws_src.key = $2
                and ws_dst.key = $3
            )
        """, str(workflow_id), str(current_status), str(new_status)
