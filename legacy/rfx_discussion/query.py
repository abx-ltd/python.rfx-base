from .types import Priority, Availability, SyncStatus
from .policy import RFXDiscussionPolicyManager
from .domain import RFXDiscussionDomain
from .state import RFXDiscussionStateManager
from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import (
    StringField,
    UUIDField,
    BooleanField,
    EnumField,
    IntegerField,
    DatetimeField,
    DictField,
    ArrayField,
)
from datetime import datetime
from . import scope

default_exclude_fields = [
    "realm",
    "deleted",
    "etag",
    "created",
    "updated",
    "creator",
    "updater",
]


class RFXDiscussionQueryManager(DomainQueryManager):
    __data_manager__ = RFXDiscussionStateManager
    __policymgr__ = RFXDiscussionPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXDiscussionDomain.Meta.namespace
        tags = RFXDiscussionDomain.Meta.tags


resource = RFXDiscussionQueryManager.register_resource
endpoint = RFXDiscussionQueryManager.register_endpoint


class ResourceScope(BaseModel):
    resource: str
    resource_id: str


@resource("inquiry")
class InquiryQuery(DomainQueryResource):
    """Inquiry listing queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "ticket"
        include_all = True
        allow_list_view = True
        allow_item_view = True
        allow_meta_view = True

        backend_model = "_inquiry"
        policy_required = "id"

    type: str = StringField("Type")
    type_icon_color: str = StringField("Type Icon Color")
    title: str = StringField("Title")
    tag_names: list[str] = ArrayField("Tag Names")
    availability: Availability = EnumField("Availability")
    activity: datetime = DatetimeField("Activity")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


# Ticket Queries


@resource("ticket")
class TicketQuery(DomainQueryResource):
    """Ticket queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "ticket"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_ticket"
        scope_required = scope.TicketScopeSchema
        policy_required = "id"

    project_id: UUID_TYPE = UUIDField("Project ID")
    title: str = StringField("Title")
    description: str = StringField("Description")
    priority: Priority = EnumField("Priority")
    type: str = StringField("Type")
    parent_id: UUID_TYPE = UUIDField("Parent ID")
    assignee: UUID_TYPE = UUIDField("Assignee")
    status: str = StringField("Status")
    availability: Availability = EnumField("Availability")
    sync_status: SyncStatus = EnumField("Sync Status")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


@resource("ticket-type")
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
@resource("tag")
class TagQuery(DomainQueryResource):
    """Tag queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "tag"
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
    organization_id: UUID_TYPE = UUIDField("Organization ID")


# Comment Queries


@resource("comment")
class CommentQuery(DomainQueryResource):
    """Comment queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment"
        scope_required = scope.CommentScopeSchema

    master_id: UUID_TYPE = UUIDField("Master ID")
    parent_id: UUID_TYPE = UUIDField("Parent ID")
    depth: int = IntegerField("Depth")
    content: str = StringField("Content")
    creator: dict = DictField("Creator")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


@resource("status")
class WorkflowStatusQuery(DomainQueryResource):
    """Workflow status queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "_status"

    entity_type: str = StringField("Entity Type")
    status_id: UUID_TYPE = UUIDField("Status ID")
    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_initial: bool = BooleanField("Is Initial")
    is_final: bool = BooleanField("Is Final")
