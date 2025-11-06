from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE


class TicketScopeSchema(BaseModel):
    project_id: UUID_TYPE = UUIDField("Project ID")


class CommentScopeSchema(BaseModel):
    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
