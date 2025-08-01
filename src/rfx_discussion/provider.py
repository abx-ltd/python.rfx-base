from fluvius.data import DataAccessManager
from fluvius.fastapi.auth import FluviusAuthProfileProvider

from .model import CPOPortalConnector


class RFXClientProfileProvider(
    FluviusAuthProfileProvider,
    DataAccessManager
):
    __connector__ = CPOPortalConnector
    __automodel__ = True
