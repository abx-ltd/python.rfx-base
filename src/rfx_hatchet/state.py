from fluvius.data import DataAccessManager
from rfx_schema.rfx_hatchet import RFXHatchetConnector
from rfx_schema.rfx_hatchet import _schema, _viewmap  # noqa: F401

class RFXHatchetStateManager(DataAccessManager):
    __connector__ = RFXHatchetConnector
    __automodel__ = True
