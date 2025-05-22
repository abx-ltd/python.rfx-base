from fluvius.domain.state import DataAccessManager
from .model import IDMConnector

class IDMStateManager(DataAccessManager):
    __connector__ = IDMConnector
    __automodel__ = True
