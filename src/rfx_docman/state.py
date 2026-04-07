from fluvius.domain.state import DataAccessManager
from rfx_schema.rfx_docman import RFXDocmanConnector, _schema  # noqa: F401
from .policy import RFXDocmanPolicy  # noqa


class RFXDocmanStateManager(DataAccessManager):
    __connector__ = RFXDocmanConnector
    __automodel__ = True