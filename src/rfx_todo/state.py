from fluvius.domain.state import DataAccessManager
from rfx_schema import RFXTodoConnector
from rfx_schema.rfx_todo import _schema  # noqa: F401


class RFXTodoStateManager(DataAccessManager):
    __connector__ = RFXTodoConnector
    __automodel__ = True
