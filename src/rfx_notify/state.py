from fluvius.domain.state import DataAccessManager
from .model import NotifyConnector


class NotifyStateManager(DataAccessManager):
    __connector__ = NotifyConnector
    __automodel__ = True
