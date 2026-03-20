from fluvius.domain.state import DataAccessManager
from rfx_schema.rfx_qr import RFXQRConnector


class QRStateManager(DataAccessManager):
    __connector__ = RFXQRConnector
    __automodel__ = True
