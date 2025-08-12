from typing import Optional

from pydantic import Field
from fluvius.data import DataModel, UUID_TYPE

from .types import Priority, Availability

# Ticket related payloads


class CreateInquiryPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    priority: Optional[Priority] = Priority.MEDIUM
    availability: Optional[Availability] = Availability.CLOSED


class CreateTicketPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    priority: str
    assignee: Optional[UUID_TYPE] = None
    parent_id: Optional[UUID_TYPE] = None


class DeleteTicketTypePayload(DataModel):
    ticket_type_id: UUID_TYPE = None


class UpdateTicketPayload(DataModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[Priority] = None
    assignee: Optional[UUID_TYPE] = None
    availability: Optional[Availability] = None
    status: Optional[str] = None


class RemoveTicketPayload(DataModel):
    ticket_id: UUID_TYPE


class ChangeTicketStatusPayload(DataModel):
    next_status: str
    note: Optional[str]


class AssignTicketMemberPayload(DataModel):
    member_id: UUID_TYPE


class RemoveTicketMemberPayload(DataModel):
    member_id: UUID_TYPE


class AddTicketCommentPayload(DataModel):
    comment_id: UUID_TYPE


class AddTicketParticipantPayload(DataModel):
    participant_id: UUID_TYPE


class AddTicketTagPayload(DataModel):
    tag_id: UUID_TYPE


class RemoveTicketTagPayload(DataModel):
    tag_id: UUID_TYPE


class CreateTicketTypePayload(DataModel):
    key: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    icon_color: Optional[str] = Field(max_length=7, default=None)
    is_active: bool = True
    is_inquiry: bool = False


# Tag related payloads
class CreateTagPayload(DataModel):
    key: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    target_resource: str


class UpdateTagPayload(DataModel):
    key: str = Field(max_length=50)
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    target_resource: Optional[str] = None
    is_active: Optional[bool] = None
