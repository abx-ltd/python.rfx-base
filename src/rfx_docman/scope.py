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

    parent_path: str = Field(..., description="Filter entries by parent folder path")


class TagScopeSchema(BaseModel):
    cabinet_id: Optional[UUID_TYPE] = Field(
        default=None, description="Filter tags by cabinet ID"
    )
    realm_id: Optional[UUID_TYPE] = Field(
        default=None, description="Filter tags by realm ID"
    )


class RealmMetaScopeSchema(BaseModel):
    realm_id: UUID_TYPE = UUIDField("Realm ID")
