from .model import RFXDiscussConnector
from fluvius.data import DataAccessManager, item_query, value_query, list_query


class RFXDiscussStateManager(DataAccessManager):
    __connector__ = RFXDiscussConnector
    __automodel__ = True

 
