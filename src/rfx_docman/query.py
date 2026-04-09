from typing import Optional

from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import (
    BooleanField,
    PrimaryID,
    StringField,
    UUIDField,
    IntegerField,
    JSONField,
)

from .domain import RFXDocmanDomain
from .state import RFXDocmanStateManager
from .policy import RFXDocmanPolicyManager
from . import scope


class RFXDocmanQueryManager(DomainQueryManager):
    __data_manager__ = RFXDocmanStateManager
    __policymgr__ = RFXDocmanPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXDocmanDomain.Meta.namespace
        tags = RFXDocmanDomain.Meta.tags


resource = RFXDocmanQueryManager.register_resource
endpoint = RFXDocmanQueryManager.register_endpoint


@resource("realm")
class RealmQuery(DomainQueryResource):
    """Realm queries."""

    class Meta(DomainQueryResource.Meta):
        resource = "realm"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        policy_required = True
        backend_model = "_realm"

    id: UUID_TYPE = PrimaryID("Realm ID")
    name: str = StringField("Name")
    description: str = StringField("Description")
    icon: str = StringField("Icon")
    color: str = StringField("Color")

    realm_meta: Optional[dict] = JSONField("Realm Meta", default=None)
    shelf_count: int = IntegerField("Shelf Count")


@resource("shelf")
class ShelfQuery(DomainQueryResource):
    """Shelf queries."""

    class Meta(DomainQueryResource.Meta):
        resource = "shelf"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_shelf"
        scope_required = scope.ShelfScopeSchema

    id: UUID_TYPE = PrimaryID("Shelf ID")
    realm_id: UUID_TYPE = UUIDField("Realm ID")
    code: str = StringField("Code")
    name: str = StringField("Name")
    description: Optional[str] = StringField("Description")

    # Aggregate information
    category_count: int = IntegerField("Category Count")


@resource("category")
class CategoryQuery(DomainQueryResource):
    """Category queries."""

    class Meta(DomainQueryResource.Meta):
        resource = "category"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_category"
        scope_required = scope.CategoryScopeSchema

    id: UUID_TYPE = PrimaryID("Category ID")
    realm_id: UUID_TYPE = UUIDField("Realm ID")
    shelf_id: UUID_TYPE = UUIDField("Shelf ID")
    code: str = StringField("Code")
    name: str = StringField("Name")
    description: Optional[str] = StringField("Description")

    # Aggregate information
    cabinet_count: int = IntegerField("Cabinet Count")


@resource("cabinet")
class CabinetQuery(DomainQueryResource):
    """Cabinet queries."""

    class Meta(DomainQueryResource.Meta):
        resource = "cabinet"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_cabinet"
        scope_required = scope.CabinetScopeSchema

    id: UUID_TYPE = PrimaryID("Cabinet ID")
    realm_id: UUID_TYPE = UUIDField("Realm ID")
    category_id: UUID_TYPE = UUIDField("Category ID")
    code: str = StringField("Code")
    name: str = StringField("Name")
    description: Optional[str] = StringField("Description")

    # Aggregate information
    entry_count: int = IntegerField("Entry Count")


@resource("entry")
class EntryQuery(DomainQueryResource):
    """Entry queries."""

    class Meta(DomainQueryResource.Meta):
        resource = "entry"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_entry"
        scope_required = scope.EntryScopeSchema

    id: UUID_TYPE = PrimaryID("Entry ID")
    cabinet_id: UUID_TYPE = UUIDField("Cabinet ID")
    path: str = StringField("Path")
    name: str = StringField("Name")
    type: str = StringField("Type")
    size: Optional[int] = IntegerField("Size")
    mime_type: Optional[str] = StringField("MIME Type")
    author_name: Optional[str] = StringField("Author Name")

    parent_path: Optional[str] = StringField("Parent Path")
    is_virtual: bool = BooleanField("Is Virtual")

    # Aggregated from entry_tag JOIN tag in _entry view
    tags: Optional[list] = JSONField("Tags", default=None)


@resource("tag")
class TagQuery(DomainQueryResource):
    """Tag queries."""

    class Meta(DomainQueryResource.Meta):
        resource = "tag"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_tag"
        scope_required = scope.TagScopeSchema

    id: UUID_TYPE = PrimaryID("Tag ID")
    cabinet_id: Optional[UUID_TYPE] = UUIDField("Cabinet ID")
    realm_id: UUID_TYPE = UUIDField("Realm ID")
    name: str = StringField("Name")
    color: Optional[str] = StringField("Color")
    icon: Optional[str] = StringField("Icon")
