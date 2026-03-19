from typing import Optional

from pydantic import Field, field_validator, model_validator
from fluvius.data import DataModel, UUID_TYPE
import re


class BaseUpdatePayload(DataModel):
    @model_validator(mode="after")
    def at_least_one_field_required(self):
        if not self.model_dump(exclude_none=True):
            raise ValueError("At least one field is required to update")


class CreateRealmPayload(DataModel):
    name: str = Field(..., description="Realm name")
    description: Optional[str] = Field(default=None, description="Realm description")
    icon: Optional[str] = Field(default=None, description="Icon identifier")
    color: Optional[str] = Field(default=None, description="Hex color code")


class UpdateRealmPayload(BaseUpdatePayload):
    name: Optional[str] = Field(default=None, description="Realm name")
    description: Optional[str] = Field(default=None, description="Realm description")
    icon: Optional[str] = Field(default=None, description="Icon identifier")
    color: Optional[str] = Field(default=None, description="Hex color code")


def validate_shelf_code(value: Optional[str]) -> Optional[str]:

    if value is None:
        return None
    code = value.strip().upper()
    if not re.match(r"^[A-Z]$", code):
        raise ValueError("Shelf code must be a single letter A -Z")
    return code


class CreateShelfPayload(DataModel):
    code: str = Field(..., description="Shelf code (A-Z)")
    name: str = Field(..., description="Shelf name")
    description: Optional[str] = Field(default=None, description="Shelf description")

    _nomaralize_code = field_validator("code")(validate_shelf_code)


class UpdateShelfPayload(BaseUpdatePayload):
    code: Optional[str] = Field(default=None, description="Shelf code (A-Z)")
    name: Optional[str] = Field(default=None, description="Shelf name")
    description: Optional[str] = Field(default=None, description="Shelf description")

    _nomaralize_code = field_validator("code")(validate_shelf_code)


class RemoveShelfPayload(DataModel):
    shelf_id: UUID_TYPE = Field(..., description="Shelf ID to remove")


def validate_category_code(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    code = value.strip().upper()
    if not re.match(r"^[A-Z][0-9]{2}$", code):
        raise ValueError("Category code must follow pattern A01 (Letter + 2 digits 01-99)")
    return code


class CreateCategoryPayload(DataModel):
    code: str = Field(..., description="Category code (e.g. A01)")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(default=None, description="Category description")

    _normalize_code = field_validator("code")(validate_category_code)


class UpdateCategoryPayload(BaseUpdatePayload):
    category_id: UUID_TYPE = Field(..., description="Category ID to update")
    code: Optional[str] = Field(default=None, description="Category code (e.g. A01)")
    name: Optional[str] = Field(default=None, description="Category name")
    description: Optional[str] = Field(default=None, description="Category description")

    _normalize_code = field_validator("code")(validate_category_code)


class RemoveCategoryPayload(DataModel):
    category_id: UUID_TYPE = Field(..., description="Category ID to remove")


def validate_cabinet_code(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    code = value.strip().upper()
    if not re.match(r"^[A-Z][0-9]{2}-[0-9]{3}$", code):
        raise ValueError("Cabinet code must follow pattern A01-001 (CategoryCode + hyphen + 3 digits)")
    return code


class CreateCabinetPayload(DataModel):
    code: str = Field(..., description="Cabinet code (e.g. A01-001)")
    name: str = Field(..., description="Cabinet name")
    description: Optional[str] = Field(default=None, description="Cabinet description")

    _normalize_code = field_validator("code")(validate_cabinet_code)


class UpdateCabinetPayload(BaseUpdatePayload):
    cabinet_id: UUID_TYPE = Field(..., description="Cabinet ID to update")
    code: Optional[str] = Field(default=None, description="Cabinet code (e.g. A01-001)")
    name: Optional[str] = Field(default=None, description="Cabinet name")
    description: Optional[str] = Field(default=None, description="Cabinet description")

    _normalize_code = field_validator("code")(validate_cabinet_code)


class RemoveCabinetPayload(DataModel):
    cabinet_id: UUID_TYPE = Field(..., description="Cabinet ID to remove")


