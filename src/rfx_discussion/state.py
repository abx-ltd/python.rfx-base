from .model import RFXDiscussionConnector
from fluvius.data import DataAccessManager, item_query


class RFXDiscussionStateManager(DataAccessManager):
    __connector__ = RFXDiscussionConnector
    __automodel__ = True

    @item_query
    def get_profile(self, profile_id):
        return """
            select * from "cpo-user"."profile"
            where _id = $1
        """, str(profile_id)
