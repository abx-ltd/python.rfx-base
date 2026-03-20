from fluvius.data import DataAccessManager
from fluvius.fastapi.auth import FluviusAuthProfileProvider

from rfx_schema.rfx_client import RFXClientConnector


class RFXClientProfileProvider(
    FluviusAuthProfileProvider,
    DataAccessManager
):
    __connector__ = RFXClientConnector
    __automodel__ = True
