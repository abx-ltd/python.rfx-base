from typing import Optional

from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import (
    PrimaryID,
    StringField,
    UUIDField,
    IntegerField,
    JSONField,
)

from .domain import RFXDocmanDomain
from .state import RFXDocmanStateManager
from . import scope


class RFXDocmanQueryManager(DomainQueryManager):
    __data_manager__ = RFXDocmanStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXDocmanDomain.Meta.namespace
        tags = RFXDocmanDomain.Meta.tags


resource = RFXDocmanQueryManager.register_resource
endpoint = RFXDocmanQueryManager.register_endpoint


@resource("realm")
class RealmQuery(DomainQueryResource):
    """Realm queries."""

    @classmethod
    def base_query(cls, context, scope):
        return {}

    class Meta(DomainQueryResource.Meta):
        resource = "realm"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

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

    @classmethod
    def base_query(cls, context, scope):
        return {"realm_id": scope["realm_id"]}

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

    @classmethod
    def base_query(cls, context, scope_data):
        return {"shelf_id": scope_data["shelf_id"]}

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

    @classmethod
    def base_query(cls, context, scope_data):
        return {"category_id": scope_data["category_id"]}

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

    @classmethod
    def base_query(cls, context, scope_data):
        query = {"cabinet_id": scope_data["cabinet_id"]}

        if (parent_path := scope_data.get("parent_path")) is not None:
            query["parent_path"] = parent_path
        return query

    class Meta(DomainQueryResource.Meta):
        resource = "entry"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "entry"
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

    @classmethod
    def base_query(cls, context, scope_data):
        query = {}
        if (cabinet_id := scope_data.get("cabinet_id")) is not None:
            query["cabinet_id"] = cabinet_id
        else:
            # Keep one canonical row per tag when not filtering by cabinet.
            query["cabinet_id"] = None
        if (realm_id := scope_data.get("realm_id")) is not None:
            query["realm_id"] = realm_id
        return query

    id: UUID_TYPE = PrimaryID("Tag ID")
    cabinet_id: Optional[UUID_TYPE] = UUIDField("Cabinet ID")
    realm_id: UUID_TYPE = UUIDField("Realm ID")
    name: str = StringField("Name")
    color: Optional[str] = StringField("Color")
    icon: Optional[str] = StringField("Icon")
