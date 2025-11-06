from fluvius.data import DataAccessManager
from fluvius.fastapi.auth import FluviusAuthProfileProvider

from .model import RFXDiscussionConnector


class RFXDiscussionProfileProvider(
    FluviusAuthProfileProvider,
    DataAccessManager
):
    __connector__ = RFXDiscussionConnector
    __automodel__ = True
