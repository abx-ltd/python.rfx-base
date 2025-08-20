from fluvius.domain.state import DataAccessManager
from fluvius.domain.logstore.sql import DomainLogConnector


class RFXCqrsStateManager(DataAccessManager):
    __connector__ = DomainLogConnector
    __automodel__ = True
