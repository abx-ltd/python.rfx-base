from fluvius.data import DataAccessManager
from fluvius.fastapi.auth import FluviusAuthProfileProvider

from rfx_schema.rfx_discuss import RFXDiscussConnector


class RFXDiscussProfileProvider(
    FluviusAuthProfileProvider,
    DataAccessManager
):
    __connector__ = RFXDiscussConnector
    __automodel__ = True
