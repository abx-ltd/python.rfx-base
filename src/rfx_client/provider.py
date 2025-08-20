from fluvius.data import DataAccessManager
from fluvius.fastapi.auth import FluviusAuthProfileProvider

from .model import RFXClientConnector


class RFXClientProfileProvider(
    FluviusAuthProfileProvider,
    DataAccessManager
):
    __connector__ = RFXClientConnector
    __automodel__ = True
