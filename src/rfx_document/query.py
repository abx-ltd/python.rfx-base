from typing import Optional

from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import PrimaryID, StringField, UUIDField

from .domain import RFXDocumentDomain
from .state import RFXDocumentStateManager
from . import scope


class RFXDocumentQueryManager(DomainQueryManager):
    __data_manager__ = RFXDocumentStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXDocumentDomain.Meta.namespace
        tags = RFXDocumentDomain.Meta.tags


resource = RFXDocumentQueryManager.register_resource
endpoint = RFXDocumentQueryManager.register_endpoint


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

        backend_model = "realm"
        # scope_required = scope.RealmScopeSchema

    id: UUID_TYPE = PrimaryID("Realm ID")
    name: str = StringField("Name")
    description: str = StringField("Description")
    icon: str = StringField("Icon")
    color: str = StringField("Color")


@resource("shelf")
class ShelfQuery(DomainQueryResource):
    """Shelf queries."""

    @classmethod
    def base_query(cls, context, scope_data):
        realm_id = scope_data.get("realm_id")
        if realm_id:
            return {"realm_id": realm_id}
        return {}

    class Meta(DomainQueryResource.Meta):
        resource = "shelf"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "shelf"
        scope_required = scope.ShelfScopeSchema

    id: UUID_TYPE = PrimaryID("Shelf ID")
    realm_id: UUID_TYPE = UUIDField("Realm ID")
    code: str = StringField("Code")
    name: str = StringField("Name")
    description: Optional[str] = StringField("Description")


@resource("category")
class CategoryQuery(DomainQueryResource):
    """Category queries."""

    @classmethod
    def base_query(cls, context, scope_data):
        realm_id = scope_data.get("realm_id")
        shelf_id = scope_data.get("shelf_id")
        query = {}
        if realm_id:
            query["realm_id"] = realm_id
        if shelf_id:
            query["shelf_id"] = shelf_id
        return query

    class Meta(DomainQueryResource.Meta):
        resource = "category"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "category"
        scope_required = scope.CategoryScopeSchema

    id: UUID_TYPE = PrimaryID("Category ID")
    realm_id: UUID_TYPE = UUIDField("Realm ID")
    shelf_id: UUID_TYPE = UUIDField("Shelf ID")
    code: str = StringField("Code")
    name: str = StringField("Name")
    description: Optional[str] = StringField("Description")


@resource("cabinet")
class CabinetQuery(DomainQueryResource):
    """Cabinet queries."""

    @classmethod
    def base_query(cls, context, scope_data):
        realm_id = scope_data.get("realm_id")
        category_id = scope_data.get("category_id")
        query = {}
        if realm_id:
            query["realm_id"] = realm_id
        if category_id:
            query["category_id"] = category_id
        return query

    class Meta(DomainQueryResource.Meta):
        resource = "cabinet"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "cabinet"
        scope_required = scope.CabinetScopeSchema

    id: UUID_TYPE = PrimaryID("Cabinet ID")
    realm_id: UUID_TYPE = UUIDField("Realm ID")
    category_id: UUID_TYPE = UUIDField("Category ID")
    code: str = StringField("Code")
    name: str = StringField("Name")
    description: Optional[str] = StringField("Description")
