from rfx_schema.rfx_2dmessage import RFX2DMessageConnector
from fluvius.data import DataAccessManager, item_query, list_query
from . import config


class RFX2DMessageStateManager(DataAccessManager):
    __connector__ = RFX2DMessageConnector
    __automodel__ = True

    # Add custom queries here as needed
    # @item_query
    # def get_message(self, message_id):
    #     ...

    # @list_query
    # def get_messages(self, message_ids):
    #     ...