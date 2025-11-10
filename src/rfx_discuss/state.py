from .model import RFXDiscussConnector
from fluvius.data import DataAccessManager, item_query, list_query
from pypika import Table
from pypika import Schema
from . import config

user_s = Schema(config.RFX_USER_SCHEMA)
user_profile = Table("profile", schema=user_s)


class RFXDiscussStateManager(DataAccessManager):
    __connector__ = RFXDiscussConnector
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
            return "SELECT * FROM {user_profile} WHERE 1=0".format(
                user_profile=user_profile
            ), ()

        placeholders = ", ".join(f"${i + 1}" for i in range(len(profile_ids)))
        query = """
            select * from {user_profile}
            where _id in ({placeholders})
        """.format(user_profile=user_profile, placeholders=placeholders)
        return query, *[str(profile_id) for profile_id in profile_ids]
