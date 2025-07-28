from fluvius.domain.state import DataAccessManager
from .model import CPOPortalConnector


class CPOPortalStateManager(DataAccessManager):
    __connector__ = CPOPortalConnector
    __automodel__ = True
