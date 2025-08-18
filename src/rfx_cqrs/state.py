from fluvius.domain.state import DataAccessManager
from .model import RFXCqrsConnector


class RFXCqrsStateManager(DataAccessManager):
    __connector__ = RFXCqrsConnector
    __automodel__ = True
