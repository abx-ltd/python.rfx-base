from fluvius.domain.state import DataAccessManager
from rfx_schema import RFXMessageConnector
from rfx_schema.rfx_message import _schema, _viewmap  # noqa: F401


class MessageStateManager(DataAccessManager):
    __connector__ = RFXMessageConnector
    __automodel__ = True
