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
