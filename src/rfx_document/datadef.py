from typing import Optional

from pydantic import Field, field_validator, model_validator
from fluvius.data import DataModel, UUID_TYPE

class CreateRealPayload(DataModel):
    name: str = Field(..., description="Realm name")
    description: Optional[str] = Field(default=None, description="Realm description")
    icon: Optional[str] = Field(default=None, description="Icon identifier")
    color: Optional[str] = Field(default=None, description="Hex color code")


class UpdateRealPayload(DataModel):
    name: Optional[str] = Field(default=None, description="Realm name")
    description: Optional[str] = Field(default=None, description="Document description")
    icon: Optional[str] = Field(default=None, description="Icon identifier")
    color: Optional[str] = Field(default=None, description="Hex color code")

    @model_validator(mode='after')
    def at_least_one_field_required(self):
        if not self.model_dump(exclude_none=True):
            raise ValueError("At least one field required")
        return self


class CreateShelfPayload(DataModel):
    realm_id: UUID_TYPE = Field(..., description="Realm ID")
    code: Optional[str] = Field(default=None, description="Shelf code (A-Z)")
    name: str = Field(..., description="Shelf name")
    description: Optional[str] = Field(default=None, description="Shelf description")

    @field_validator("code")
    @classmethod
    def normalize_shelf_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        code = value.strip().upper()
        if len(code) != 1 or not code.isalpha() or not code.isascii():
            raise ValueError("Shelf code must be a single letter A-Z")
        return code


class UpdateShelfPayload(DataModel):
    code: Optional[str] = Field(default=None, description="Shelf code (A-Z)")
    name: Optional[str] = Field(default=None, description="Shelf name")
    description: Optional[str] = Field(default=None, description="Shelf description")

    @field_validator("code")
    @classmethod
    def normalize_shelf_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        code = value.strip().upper()
        if len(code) != 1 or not code.isalpha() or not code.isascii():
            raise ValueError("Shelf code must be a single letter A-Z")
        return code

    @model_validator(mode='after')
    def at_least_one_field_required(self):
        if not self.model_dump(exclude_none=True):
            raise ValueError("At least one field required")
        return self