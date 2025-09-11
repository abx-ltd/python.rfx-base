from typing import Optional

from pydantic import Field
from fluvius.data import DataModel, UUID_TYPE

from .types import Priority, Availability


# ---------- Inquiry (Ticket Context) ----------
class CreateInquiryPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    priority: Optional[Priority] = Priority.MEDIUM
    availability: Optional[Availability] = Availability.CLOSED


# ---------- Ticket (Ticket Context) ----------
class CreateTicketPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    priority: str
    assignee: Optional[UUID_TYPE] = None
    parent_id: Optional[UUID_TYPE] = None
    availability: Optional[Availability] = Availability.OPEN


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


# ---------- Ticket Assignee (Ticket Context) ----------
class AssignTicketMemberPayload(DataModel):
    member_id: UUID_TYPE


class RemoveTicketMemberPayload(DataModel):
    member_id: UUID_TYPE


# ---------- Ticket Participant (Ticket Context) ----------
class AddTicketParticipantPayload(DataModel):
    participant_id: UUID_TYPE


class RemoveTicketParticipantPayload(DataModel):
    participant_id: UUID_TYPE


# ---------- Ticket Tag (Ticket Context) ----------
class AddTicketTagPayload(DataModel):
    tag_id: UUID_TYPE


class RemoveTicketTagPayload(DataModel):
    tag_id: UUID_TYPE


# ---------- Ticket Type (Ticket Context) ----------
class CreateTicketTypePayload(DataModel):
    key: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    icon_color: Optional[str] = Field(max_length=7, default=None)
    is_active: bool = True
    is_inquiry: bool = False


class UpdateTicketTypePayload(DataModel):
    ticket_type_id: UUID_TYPE
    key: str = Field(max_length=50)
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    icon_color: Optional[str] = Field(max_length=7, default=None)
    is_active: Optional[bool] = None
    is_inquiry: Optional[bool] = None


class DeleteTicketTypePayload(DataModel):
    ticket_type_id: UUID_TYPE = None


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

# ---------- Comment Context ----------


class CreateCommentPayload(DataModel):
    content: str


class UpdateCommentPayload(DataModel):
    content: str

# ---------- Ticket Comment (Ticket Context) ----------


class CreateTicketCommentPayload(DataModel):
    content: str


class ReplyToCommentPayload(DataModel):
    content: str

# ---------- Status Context ----------


class CreateStatusPayload(DataModel):
    name: str
    description: Optional[str] = None
    entity_type: str
    is_active: bool = True


class CreateStatusKeyPayload(DataModel):
    key: str
    name: str
    description: Optional[str] = None
    is_initial: bool = False
    is_final: bool = False


class CreateStatusTransitionPayload(DataModel):
    src_status_key_id: UUID_TYPE
    dst_status_key_id: UUID_TYPE
    condition: Optional[dict] = None
