from .model import RFXDiscussConnector
from fluvius.data import DataAccessManager, item_query, value_query, list_query


class RFXDiscussStateManager(DataAccessManager):
    __connector__ = RFXDiscussConnector
    __automodel__ = True

    @item_query
    def get_profile(self, profile_id):
        return """
            select * from "cpo-user"."profile"
            where _id = $1
        """, str(profile_id)

    @value_query
    def has_status_transition(self, workflow_id, current_status_id, new_status_id):
        return """
            select exists (
                select 1
                from "cpo-Discuss"."status-transition" st
                join "cpo-Discuss"."status-key" ws_src on ws_src._id = st.src_status_key_id
                join "cpo-Discuss"."status-key" ws_dst on ws_dst._id = st.dst_status_key_id
                where st.status_id = $1
                and st.src_status_key_id = $2
                and st.dst_status_key_id = $3
            )
        """, str(workflow_id), str(current_status_id), str(new_status_id)
        
    @value_query
    def get_project_id_by_ticket_id(self, ticket_id):
        """
        Lấy project_id từ bảng project-ticket bằng ticket_id.
        """
        return """
            SELECT project_id FROM "cpo-client"."project-ticket"
            WHERE ticket_id = $1
        """, str(ticket_id)
        
    @list_query
    def get_ticket_ids_by_project_id(self, project_id):
        """
        Lấy danh sách ticket_id từ bảng project-ticket (schema cpo-client).
        """
        return """
            SELECT ticket_id FROM "cpo-client"."project-ticket"
            WHERE project_id = $1
        """, str(project_id)

    @list_query
    def get_tickets_by_ids(self, ticket_ids: list):
        """
        Lấy thông tin chi tiết của các ticket dựa trên danh sách ID.
        """
        return """
            SELECT * FROM "cpo-Discuss"."ticket"
            WHERE _id = ANY($1)
        """, ticket_ids
