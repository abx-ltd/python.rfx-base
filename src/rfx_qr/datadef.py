from typing import Optional

from fluvius.data import DataModel, Field

class CreateQRCodePayload(DataModel):
    transaction_amount: Optional[float] = Field(
        None, description="Amount for the QR code transaction."
    )
    transaction_id: Optional[str] = Field(None, description="Unique identifier for the transaction.")
    purpose_of_transaction: Optional[str] = Field(None, description="Purpose of the transaction.")
    bill_number: Optional[str] = Field(None, description="Bill number associated with the QR code.")
    mobile_number: Optional[str] = Field(None, description="Mobile number of the payer.")
    customer_label: Optional[str] = Field(None, description="Label for the customer.")
