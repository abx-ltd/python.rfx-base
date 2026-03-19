from typing import Optional

from fluvius.data import UUID_TYPE
from pydantic import BaseModel


class RealmScopeSchema(BaseModel):
    pass


class ShelfScopeSchema(BaseModel):
    realm_id: Optional[UUID_TYPE] = None


class CategoryScopeSchema(BaseModel):
    realm_id: Optional[UUID_TYPE] = None
    shelf_id: Optional[UUID_TYPE] = None


class CabinetScopeSchema(BaseModel):
    realm_id: Optional[UUID_TYPE] = None
    category_id: Optional[UUID_TYPE] = None
