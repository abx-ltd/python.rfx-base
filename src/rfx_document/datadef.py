import re
from typing import Optional
from pydantic import Field, field_validator, model_validator
from fluvius.data import DataModel, UUID_TYPE
from .types import EntryTypeEnum


class BaseUpdatePayload(DataModel):
    """Base payload for update operations to ensure at least one field is provided."""
    
    @model_validator(mode="after")
    def at_least_one_field_required(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field is required to update")
        
        return self


# ==========================================
# REALM PAYLOADS
# ==========================================

class CreateRealmPayload(DataModel):
    name: str = Field(..., description="Realm name", examples=["Corporate Hub"])
    description: Optional[str] = Field(default=None, description="Detailed description of the realm", examples=["Main repository for corporate documents"])
    icon: Optional[str] = Field(default=None, description="Lucide icon identifier", examples=["building-2"])
    color: Optional[str] = Field(default=None, description="Hex color code", examples=["#2563EB"])


class UpdateRealmPayload(BaseUpdatePayload):
    name: Optional[str] = Field(default=None, description="Realm name", examples=["Corporate Hub V2"])
    description: Optional[str] = Field(default=None, description="Detailed description of the realm")
    icon: Optional[str] = Field(default=None, description="Lucide icon identifier")
    color: Optional[str] = Field(default=None, description="Hex color code")


# ==========================================
# SHELF PAYLOADS
# ==========================================

def validate_shelf_code(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    code = value.strip().upper()
    if not re.match(r"^[A-Z]$", code):
        raise ValueError("Shelf code must be a single letter (e.g., A, B, C)")
    return code


class CreateShelfPayload(DataModel):
    code: str = Field(..., description="Single uppercase letter code", examples=["A"])
    name: str = Field(..., description="Shelf name", examples=["Governance & Management"])
    description: Optional[str] = Field(default=None, description="Shelf description")

    _normalize_code = field_validator("code")(validate_shelf_code)


class UpdateShelfPayload(BaseUpdatePayload):
    code: Optional[str] = Field(default=None, description="Single uppercase letter code", examples=["B"])
    name: Optional[str] = Field(default=None, description="Shelf name")
    description: Optional[str] = Field(default=None, description="Shelf description")

    _normalize_code = field_validator("code")(validate_shelf_code)


# ==========================================
# CATEGORY PAYLOADS
# ==========================================

def validate_category_code(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    code = value.strip().upper()
    if not re.match(r"^[A-Z][0-9]{2}$", code):
        raise ValueError("Category code must follow pattern A01 (Letter + 2 digits)")
    return code


class CreateCategoryPayload(DataModel):
    code: str = Field(..., description="Category code starting with Shelf code", examples=["A01"])
    name: str = Field(..., description="Category name", examples=["Strategic Planning"])
    description: Optional[str] = Field(default=None, description="Category description")

    _normalize_code = field_validator("code")(validate_category_code)


class UpdateCategoryPayload(BaseUpdatePayload):
    category_id: UUID_TYPE = Field(..., description="ID of the category to update")
    code: Optional[str] = Field(default=None, description="Category code starting with Shelf code", examples=["A02"])
    name: Optional[str] = Field(default=None, description="Category name")
    description: Optional[str] = Field(default=None, description="Category description")

    _normalize_code = field_validator("code")(validate_category_code)


# ==========================================
# CABINET PAYLOADS
# ==========================================

def validate_cabinet_code(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    code = value.strip().upper()
    if not re.match(r"^[A-Z][0-9]{2}-[0-9]{3}$", code):
        raise ValueError("Cabinet code must follow pattern A01-001 (CategoryCode + hyphen + 3 digits)")
    return code


class CreateCabinetPayload(DataModel):
    code: str = Field(..., description="Cabinet code including Category prefix", examples=["A01-001"])
    name: str = Field(..., description="Cabinet name", examples=["Annual Reports 2026"])
    description: Optional[str] = Field(default=None, description="Cabinet description")

    _normalize_code = field_validator("code")(validate_cabinet_code)


class UpdateCabinetPayload(BaseUpdatePayload):
    cabinet_id: UUID_TYPE = Field(..., description="ID of the cabinet to update")
    code: Optional[str] = Field(default=None, description="Cabinet code including Category prefix", examples=["A01-002"])
    name: Optional[str] = Field(default=None, description="Cabinet name")
    description: Optional[str] = Field(default=None, description="Cabinet description")

    _normalize_code = field_validator("code")(validate_cabinet_code)


# ==========================================
# ENTRY PAYLOADS (FILE / FOLDER)
# ==========================================

class CreateEntryPayload(DataModel):
    parent_path: str = Field(
        default="", 
        description="Parent folder path. Leave empty if creating at the root of the cabinet.",
        examples=["", "Strategic_Plans/2026"]
    )
    name: str = Field(
        ..., 
        description="Name of the file or folder (without slashes)", 
        examples=["Q1_Report.pdf", "Drafts"]
    )
    type: EntryTypeEnum = Field(
        ..., 
        description="Entry type (e.g., folder, document, pdf, image)",
        examples=["pdf"]
    )
    size: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="File size in bytes. MUST be null if type is 'folder'.",
        examples=[1048576]
    )
    mime_type: Optional[str] = Field(
        default=None, 
        description="MIME type of the file. MUST be null if type is 'folder'.",
        examples=["application/pdf"]
    )
    author: Optional[str] = Field(
        default=None, 
        description="Author or creator of the entry",
        examples=["John Doe"]
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if "/" in v or "\\" in v:
            raise ValueError("Name cannot contain slash '/' or backslash '\\' characters")
        return v.strip()

    @field_validator("parent_path")
    @classmethod
    def normalize_parent_path(cls, v: str) -> str:
        if v:
            # Remove trailing/leading slashes and replace multiple slashes with a single one
            cleaned = v.strip("/")
            return re.sub(r"/+", "/", cleaned)
        return v

    @model_validator(mode="after")
    def validate_logic_by_type(self):
        if self.type == EntryTypeEnum.FOLDER:
            if self.size is not None or self.mime_type is not None:
                raise ValueError("A folder cannot have 'size' or 'mime_type' attributes")
        return self

    @property
    def computed_path(self) -> str:
        """Utility property to generate the absolute path for database storage."""
        if not self.parent_path:
            return self.name
        return f"{self.parent_path}/{self.name}"