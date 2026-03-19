from fluvius.domain.aggregate import Aggregate, action
from datetime import timedelta

from fluvius.data import serialize_mapping, timestamp, UUID_GENR
from .qr import BaseQRGenerator

class QRAggregate(Aggregate):
    """Aggregate for QR-related operations."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._qr_generator = None

    @property
    def qr_generator(self):
        """Lazy-loaded QR generator."""
        if self._qr_generator is None:
            self._qr_generator = BaseQRGenerator()
        return self._qr_generator

    @action("qr-code-created", resources="qr_code")
    async def create_qr_code(self, data):
        """Create a new QR code with the given transaction data."""
        transaction_id = data.pop("transaction_id", None)
        qr_code = self.qr_generator.code(transaction=data)

        qr_code_record = self.init_resource(
            "qr_code",
            _id=UUID_GENR(),
            transaction_id=transaction_id,
            amount=data.get("transaction_amount"),
            currency="VND",
            payload=data,
            status="CREATED",
            expires_at=timestamp() + timedelta(hours=1),
            qr_code=qr_code
        )
        await self.statemgr.insert(qr_code_record)
        return {
            "qr_code_id": qr_code_record._id,
            "qr_code": qr_code_record.qr_code,
            "status": qr_code_record.status
        }





