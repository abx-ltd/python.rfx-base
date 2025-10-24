from .types import Priority, Availability, SyncStatus
from .policy import RFXDiscussPolicyManager
from .domain import RFXDiscussDomain
from .state import RFXDiscussStateManager
from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import StringField, UUIDField, BooleanField, EnumField, PrimaryID, IntegerField, FloatField, DatetimeField, ListField, DictField, ArrayField
from datetime import datetime
from . import scope

default_exclude_fields = ["realm", "deleted", "etag",
                          "created", "updated", "creator", "updater"]


class RFXDiscussQueryManager(DomainQueryManager):
    __data_manager__ = RFXDiscussStateManager
    __policymgr__ = RFXDiscussPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXDiscussDomain.Meta.prefix
        tags = RFXDiscussDomain.Meta.tags


resource = RFXDiscussQueryManager.register_resource
endpoint = RFXDiscussQueryManager.register_endpoint


class ResourceScope(BaseModel):
    resource: str
    resource_id: str


# Comment Queries


@resource('comment')
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