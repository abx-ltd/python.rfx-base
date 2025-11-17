from fluvius.domain.state import DataAccessManager
from .model import PolicyConnector


class PolicyStateManager(DataAccessManager):
    __connector__ = PolicyConnector
    __automodel__ = True
