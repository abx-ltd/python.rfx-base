from typing import Optional
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE
from pydantic import BaseModel, Field



class RealmScopeSchema(BaseModel):
    pass


class ShelfScopeSchema(BaseModel):
    realm_id: UUID_TYPE = UUIDField("Realm ID")


class CategoryScopeSchema(BaseModel):
    shelf_id: UUID_TYPE = UUIDField("Shelf ID")


class CabinetScopeSchema(BaseModel):
    category_id: UUID_TYPE = UUIDField("Category ID")

class EntryScopeSchema(BaseModel):
    cabinet_id: UUID_TYPE = UUIDField("Cabinet ID")

    parent_path: Optional[str] = Field(default=None, description="Filter entries by parent folder path")

