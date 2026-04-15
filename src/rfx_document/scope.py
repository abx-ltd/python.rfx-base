from typing import Optional

from fluvius.data import UUID_TYPE
from pydantic import BaseModel


class RealmScopeSchema(BaseModel):
    pass


class ShelfScopeSchema(BaseModel):
    realm_id: Optional[UUID_TYPE] = None
