from .model import RFXDiscussionConnector
from fluvius.data import DataAccessManager, item_query, value_query


class RFXDiscussionStateManager(DataAccessManager):
    __connector__ = RFXDiscussionConnector
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
                from "cpo-discussion"."status-transition" st
                join "cpo-discussion"."status-key" ws_src on ws_src._id = st.src_status_key_id
                join "cpo-discussion"."status-key" ws_dst on ws_dst._id = st.dst_status_key_id
                where st.status_id = $1
                and st.src_status_key_id = $2
                and st.dst_status_key_id = $3
            )
        """, str(workflow_id), str(current_status_id), str(new_status_id)
