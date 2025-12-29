from fluvius.data import UUID_TYPE, UUID_GENR
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import StringField, UUIDField, BooleanField, EnumField, PrimaryID
from fastapi import Request

import base64
import io
import segno

from .state import QRStateManager
from .domain import QRServiceDomain

class QRQueryManager(DomainQueryManager):
    __data_manager__ = QRStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = QRServiceDomain.Meta.prefix
        tags = QRServiceDomain.Meta.tags


resource = QRQueryManager.register_resource
endpoint = QRQueryManager.register_endpoint

@endpoint('.qr-code/{qr_code_id}')
async def get_qr_code_by_id(query_manager: QRQueryManager, request: Request, qr_code_id: str):
    """Retrieve a QR code by its unique identifier."""
    async with query_manager.data_manager.transaction():
        try:
            qr_code = await query_manager.data_manager.fetch('qr_code', qr_code_id)
        except Exception as e:
            return {"error": "QR code not found."}
        qr_img = segno.make_qr(qr_code.qr_code)
        buffer = io.BytesIO()
        qr_img.save(buffer, kind="png")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        return {
            "qr_code_id": qr_code_id,
            "qr_code": qr_code.qr_code,
            "qr_image_uri": f"data:image/png;base64,{qr_base64}",
        }
