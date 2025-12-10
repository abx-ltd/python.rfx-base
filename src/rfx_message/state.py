from fluvius.domain.state import DataAccessManager
from rfx_schema import RFXMessageConnector

class MessageStateManager(DataAccessManager):
    __connector__ = RFXMessageConnector
    __automodel__ = True
