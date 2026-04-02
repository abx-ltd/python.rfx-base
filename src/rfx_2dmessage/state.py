from fluvius.domain.state import DataAccessManager
from rfx_schema.rfx_2dmessage import RFX2DMessageConnector
from rfx_schema.rfx_2dmessage import _schema, _viewmap  # noqa: F401
from fluvius.data import value_query
from rfx_base import config
from uuid import UUID
from typing import List


class RFX2DMessageStateManager(DataAccessManager):
    __connector__ = RFX2DMessageConnector
    __automodel__ = True

    @value_query
    def get_user_ids_from_profile_ids(self, profile_ids: List[UUID]) -> List[UUID]:
        query = f"""
            SELECT coalesce(array_agg(user_id), array[]::uuid[]) AS user_ids
            FROM {config.RFX_USER_SCHEMA}.profile
            WHERE _id = ANY(CAST($1 AS uuid[]));
        """
        return (query, [str(profile_id) for profile_id in profile_ids])