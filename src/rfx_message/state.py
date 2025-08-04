from fluvius.domain.state import DataAccessManager
from .model import MessageConnector

class MessageStateManager(DataAccessManager):
    __connector__ = MessageConnector
    __automodel__ = True