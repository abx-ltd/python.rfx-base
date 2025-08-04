from fluvius.domain.state import DataAccessManager
from .model import RFXDiscussionConnector


class RFXDiscussionStateManager(DataAccessManager):
    __connector__ = RFXDiscussionConnector
    __automodel__ = True
