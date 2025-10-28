from .model import RFXDiscussConnector
from fluvius.data import DataAccessManager


class RFXDiscussStateManager(DataAccessManager):
    __connector__ = RFXDiscussConnector
    __automodel__ = True
