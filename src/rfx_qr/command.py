from .domain import QRServiceDomain
from . import datadef
from .types import QRCodeStatusEnum, QRScanResultEnum, QRRedemptionStatusEnum
from fluvius.data import serialize_mapping

processor = QRServiceDomain.command_processor
Command = QRServiceDomain.Command

class CreateQRCodeCommand(Command):
    """Command to create a new QR code."""
    class Meta:
        name = "create-qr-code"
        new_resource = True
        resources = ("qr_code",)
        tags = ["qr", "create"]
        auth_required = True
        policy_required = False

    Data = datadef.CreateQRCodePayload

    async def _process(self, agg, stm, payload):
        """Process the create QR code command."""
        transaction_data = serialize_mapping(payload)
        result = await agg.create_qr_code(transaction_data)

        yield agg.create_response({
            "qr_code_id": result["qr_code_id"],
            "qr_code": result["qr_code"],
            "status": result["status"]
        }, _type="qr-service-response")


