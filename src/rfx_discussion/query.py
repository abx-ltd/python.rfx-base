from .types import Priority, Availability, SyncStatus
from .policy import RFXDiscussionPolicyManager
from .domain import RFXDiscussionDomain
from .state import RFXDiscussionStateManager
from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import StringField, UUIDField, BooleanField, EnumField, PrimaryID, IntegerField, FloatField, DatetimeField, ListField, DictField, ArrayField
from datetime import datetime


default_exclude_fields = ["realm", "deleted", "etag",
                          "created", "updated", "creator", "updater"]


class RFXDiscussionQueryManager(DomainQueryManager):
    __data_manager__ = RFXDiscussionStateManager
    __policymgr__ = RFXDiscussionPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXDiscussionDomain.Meta.prefix
        tags = RFXDiscussionDomain.Meta.tags


resource = RFXDiscussionQueryManager.register_resource
endpoint = RFXDiscussionQueryManager.register_endpoint


class ResourceScope(BaseModel):
    resource: str
    resource_id: str

# Ticket Queries


@resource('ticket')
class TicketQuery(DomainQueryResource):
    """Ticket queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    title: str = StringField("Title")
    description: str = StringField("Description")
    priority: Priority = EnumField("Priority")
    type: str = StringField("Type")
    parent_id: UUID_TYPE = UUIDField("Parent ID")
    assignee: UUID_TYPE = UUIDField("Assignee")
    status: str = StringField("Status")
    workflow_id: UUID_TYPE = UUIDField("Workflow ID")
    availability: Availability = EnumField("Availability")
    sync_status: SyncStatus = EnumField("Sync Status")
    is_inquiry: bool = BooleanField("Is Inquiry")


@resource('ticket-status')
class TicketStatusQuery(DomainQueryResource):
    """Ticket status queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    src_state: str = StringField("Source State")
    dst_state: str = StringField("Destination State")
    note: str = StringField("Note")


@resource('inquiry')
class InquiryQuery(DomainQueryResource):
    """Inquiry listing queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_list_view = True
        allow_item_view = True
        allow_meta_view = True
        backend_model = "_inquiry"

    type: str = StringField("Type")
    type_icon_color: str = StringField("Type Icon Color")
    title: str = StringField("Title")
    tag_names: list[str] = ArrayField("Tag Names")
    availability: Availability = EnumField("Availability")
    activity: datetime = DatetimeField("Activity")


@resource('ticket-comment')
class TicketCommentQuery(DomainQueryResource):
    """Ticket comment queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    comment_id: UUID_TYPE = UUIDField("Comment ID")
    role: str = StringField("Role")


@resource('ticket-assignee')
class TicketAssigneeQuery(DomainQueryResource):
    """Ticket assignee queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    member_id: UUID_TYPE = UUIDField("Member ID")
    role: str = StringField("Role")


@resource('ticket-participants')
class TicketParticipantsQuery(DomainQueryResource):
    """Ticket participants queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    ticket_id: UUID_TYPE = UUIDField("Ticket ID")
    participant_id: UUID_TYPE = UUIDField("Participant ID")


@resource('ticket-type')
class RefTicketTypeQuery(DomainQueryResource):
    """Ticket type reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        excluded_fields = default_exclude_fields
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--ticket-type"

    name: str = StringField("Name")
    description: str = StringField("Description")
    icon_color: str = StringField("Icon Color")
    is_active: bool = BooleanField("Is Active")
    is_inquiry: bool = BooleanField("Is Inquiry")


# Tag Queries
@resource('tag')
class TagQuery(DomainQueryResource):
    """Tag queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")
    target_resource: str = StringField("Target Resource")
    target_resource_id: str = StringField("Target Resource ID")
