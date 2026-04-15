# Query scope definitions
# Define Pydantic models for query filters here

from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE

class MailboxScope(BaseModel):
    mailbox_id: UUID_TYPE = UUIDField("Mailbox ID")

