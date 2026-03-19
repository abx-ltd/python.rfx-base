from .generator import QRGenerator
from . import config

generator_config = {
    "bin_id": str(config.QR_BIN_ID),
    "consumer_id": str(config.QR_CONSUMER_ID),
    "service_code": str(config.QR_SERVICE_CODE),
    "point_of_initiation_method": str(config.QR_POINT_OF_INITIATION_METHOD),
    "transaction_currency": str(config.QR_TRANSACTION_CURRENCY),
    "store_label": str(config.QR_STORE_LABEL),
    "reference_label": str(config.QR_REFERENCE_LABEL)
}
class BaseQRGenerator(QRGenerator):
    __qr_config__ = generator_config
