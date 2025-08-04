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
    availability: Optional[Availability] = Availability.OPEN


class CreateProjectTicketPayload(DataModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    type: str
    priority: Optional[Priority] = Priority.MEDIUM
    assignee: Optional[UUID_TYPE] = None
    parent_id: Optional[UUID_TYPE] = None
    project_id: UUID_TYPE


class UpdateInquiryPayload(DataModel):
    title: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[Priority] = None
    availability: Optional[Availability] = None


class UpdateTicketPayload(DataModel):
    title: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[Priority] = None
    assignee: Optional[UUID_TYPE] = None


class ChangeTicketStatusPayload(DataModel):
    next_status: str
    note: Optional[str] = None


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

# Tag related payloads


class CreateTagPayload(DataModel):
    key: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    target_resource: str


class CreateTicketTypePayload(DataModel):
    key: str = Field(max_length=50)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    icon_color: Optional[str] = Field(max_length=7, default=None)
    is_active: bool = True
    is_inquiry: bool = False


class UpdateTagPayload(DataModel):
    code: str = Field(max_length=50)
    name: Optional[str] = Field(max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
