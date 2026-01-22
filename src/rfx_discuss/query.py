from .policy import RFXDiscussPolicyManager
from .domain import RFXDiscussDomain
from .state import RFXDiscussStateManager
from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import (
    StringField,
    UUIDField,
    IntegerField,
    DictField,
    BooleanField,
)
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


class RFXDiscussQueryManager(DomainQueryManager):
    __data_manager__ = RFXDiscussStateManager
    __policymgr__ = RFXDiscussPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXDiscussDomain.Meta.namespace
        tags = RFXDiscussDomain.Meta.tags


resource = RFXDiscussQueryManager.register_resource
endpoint = RFXDiscussQueryManager.register_endpoint


class ResourceScope(BaseModel):
    resource: str
    resource_id: str


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
    resource: str = StringField("Resource Type")
    resource_id: UUID_TYPE = UUIDField("Resource ID")

    attachment_count: int = IntegerField("Attachment Count")
    reaction_count: int = IntegerField("Reaction Count")
    flag_count: int = IntegerField("Flag Count")


@resource("comment-attachment")
class CommentAttachmentQuery(DomainQueryResource):
    """Comment Attachment queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment-attachment"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment_attachment"
        scope_required = scope.CommentAttachmentScopeSchema

    comment_id: UUID_TYPE = UUIDField("Comment ID", filterable=True)
    media_entry_id: UUID_TYPE = UUIDField("Media Entry ID", filterable=True)
    attachment_type: str = StringField("Attachment Type", filterable=True)
    caption: str = StringField("Caption")
    display_order: int = IntegerField("Display Order")
    is_primary: bool = BooleanField("Is Primary")


@resource("comment-reaction")
class CommentReactionQuery(DomainQueryResource):
    """Comment Reaction queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment-reaction"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment_reaction"
        scope_required = scope.ReactionScopeSchema

    comment_id: UUID_TYPE = UUIDField("Comment ID", filterable=True)
    user_id: UUID_TYPE = UUIDField("User ID", filterable=True)
    reaction_type: str = StringField("Reaction Type", filterable=True)
    reactor: dict = DictField("Reactor")


@resource("comment-reaction-summary")
class CommentReactionSummaryQuery(DomainQueryResource):
    """Comment Reaction Summary queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment-reaction-summary"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment_reaction_summary"
        scope_required = scope.ReactionScopeSchema

    comment_id: UUID_TYPE = UUIDField("Comment ID", filterable=True)
    reaction_type: str = StringField("Reaction Type", filterable=True)
    reaction_count: int = IntegerField("Reaction Count")
    users: dict = DictField("Users")


@resource("comment-flag")
class CommentFlagQuery(DomainQueryResource):
    """Comment Flag queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment-flag"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment_flag"
        scope_required = scope.FlagScopeSchema

    comment_id: UUID_TYPE = UUIDField("Comment ID", filterable=True)
    reported_by_user_id: UUID_TYPE = UUIDField("Reporter User ID", filterable=True)
    reason: str = StringField("Reason", filterable=True)
    status: str = StringField("Status", filterable=True)
    description: str = StringField("Description", searchable=True)
    reporter: dict = DictField("Reporter")
    comment_preview: dict = DictField("Comment Preview")


@resource("comment-flag-resolution")
class CommentFlagResolutionQuery(DomainQueryResource):
    """Comment Flag resolution queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment-flag-resolution"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment_flag_resolution"
        scope_required = scope.FlagScopeSchema

    flag_id: UUID_TYPE = UUIDField("Flag ID", filterable=True)
    resolve_by_user_id: UUID_TYPE = UUIDField("Resolved By User ID", filterable=True)
    resolved_at: str = StringField("Resolved At", filterable=True)
    resolution_note: str = StringField("Resolution Note", searchable=True)
    resolution_action: str = StringField("Resolution Action", filterable=True)
    resolver: dict = DictField("Resolver")
    flag_info: dict = DictField("Flag Info")


@resource("comment-flag-summary")
class CommentFlagSummaryQuery(DomainQueryResource):
    """Comment Flag summary queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment-flag-summary"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment_flag_summary"
        scope_required = scope.FlagScopeSchema

    comment_id: UUID_TYPE = UUIDField("Comment ID", filterable=True)
    total_flags: int = IntegerField("Total Flags")
    pending_flags: int = IntegerField("Pending Flags")
    resolved_flags: int = IntegerField("Resolved Flags")
    rejected_flags: int = IntegerField("Rejected Flags")
    flag_reasons: dict = DictField("Flag Reasons")
    latest_flag_at: str = StringField("Latest Flag At")
