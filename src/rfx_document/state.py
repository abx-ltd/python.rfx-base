from fluvius.domain.state import DataAccessManager
from rfx_schema.rfx_document import RFXDocumentConnector, _schema  # noqa: F401

class RFXDocumentStateManager(DataAccessManager):
    __connector__ = RFXDocumentConnector
    __automodel__ = True