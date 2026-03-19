import re
from typing import Optional, Annotated
from pydantic import Field, model_validator, AfterValidator
from fluvius.data import DataModel
from .types import EntryTypeEnum


class BaseUpdatePayload(DataModel):
    """Base payload for update operations to ensure at least one field is provided."""

    @model_validator(mode="after")
    def at_least_one_field_required(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field is required to update")
        return self


# ==========================================
# CUSTOM TYPES (ANNOTATED VALIDATORS)
# ==========================================


def validate_shelf_code(code: str) -> str:
    code = code.strip().upper()
    if not re.match(r"^[A-Z]$", code):
        raise ValueError("Shelf code must be a single letter (e.g., A, B, C)")
    return code


def validate_category_code(code: str) -> str:
    code = code.strip().upper()
    if not re.match(r"^[A-Z][0-9]{2}$", code):
        raise ValueError("Category code must follow pattern A01 (Letter + 2 digits)")
    return code


def validate_cabinet_code(code: str) -> str:
    code = code.strip().upper()
    if not re.match(r"^[A-Z][0-9]{2}-[0-9]{3}$", code):
        raise ValueError(
            "Cabinet code must follow pattern A01-001 (CategoryCode + hyphen + 3 digits)"
        )
    return code


def validate_entry_name(name: str) -> str:
    if "/" in name or "\\" in name:
        raise ValueError("Name cannot contain slash '/' or backslash '\\' characters")
    stripped = name.strip()
    if not stripped:
        raise ValueError("Name cannot be empty")
    return stripped


def normalize_parent_path(path: str) -> str:
    if path:
        cleaned = path.strip("/")
        return re.sub(r"/+", "/", cleaned)
    return path


ShelfCode = Annotated[str, AfterValidator(validate_shelf_code)]
CategoryCode = Annotated[str, AfterValidator(validate_category_code)]
CabinetCode = Annotated[str, AfterValidator(validate_cabinet_code)]
EntryName = Annotated[str, AfterValidator(validate_entry_name)]
ParentPath = Annotated[str, AfterValidator(normalize_parent_path)]


# ==========================================
# REALM PAYLOADS
# ==========================================


class CreateRealmPayload(DataModel):
    name: str = Field(..., description="Realm name", examples=["Corporate Hub"])
    description: Optional[str] = Field(
        default=None, description="Detailed description of the realm"
    )
    icon: Optional[str] = Field(
        default=None, description="Lucide icon identifier", examples=["building-2"]
    )
    color: Optional[str] = Field(
        default=None, description="Hex color code", examples=["#2563EB"]
    )


class UpdateRealmPayload(BaseUpdatePayload):
    name: Optional[str] = Field(default=None, description="Realm name")
    description: Optional[str] = Field(
        default=None, description="Detailed description of the realm"
    )
    icon: Optional[str] = Field(default=None, description="Lucide icon identifier")
    color: Optional[str] = Field(default=None, description="Hex color code")


# ==========================================
# SHELF PAYLOADS
# ==========================================


class CreateShelfPayload(DataModel):
    code: ShelfCode = Field(
        ..., description="Single uppercase letter code", examples=["A"]
    )
    name: str = Field(
        ..., description="Shelf name", examples=["Governance & Management"]
    )
    description: Optional[str] = Field(default=None, description="Shelf description")


class UpdateShelfPayload(BaseUpdatePayload):
    code: Optional[ShelfCode] = Field(
        default=None, description="Single uppercase letter code", examples=["B"]
    )
    name: Optional[str] = Field(default=None, description="Shelf name")
    description: Optional[str] = Field(default=None, description="Shelf description")


# ==========================================
# CATEGORY PAYLOADS
# ==========================================


class CreateCategoryPayload(DataModel):
    code: CategoryCode = Field(
        ..., description="Category code starting with Shelf code", examples=["A01"]
    )
    name: str = Field(..., description="Category name", examples=["Strategic Planning"])
    description: Optional[str] = Field(default=None, description="Category description")


class UpdateCategoryPayload(BaseUpdatePayload):
    code: Optional[CategoryCode] = Field(
        default=None,
        description="Category code starting with Shelf code",
        examples=["A02"],
    )
    name: Optional[str] = Field(default=None, description="Category name")
    description: Optional[str] = Field(default=None, description="Category description")


# ==========================================
# CABINET PAYLOADS
# ==========================================


class CreateCabinetPayload(DataModel):
    code: CabinetCode = Field(
        ..., description="Cabinet code including Category prefix", examples=["A01-001"]
    )
    name: str = Field(..., description="Cabinet name", examples=["Annual Reports 2026"])
    description: Optional[str] = Field(default=None, description="Cabinet description")


class UpdateCabinetPayload(BaseUpdatePayload):
    code: Optional[CabinetCode] = Field(
        default=None,
        description="Cabinet code including Category prefix",
        examples=["A01-002"],
    )
    name: Optional[str] = Field(default=None, description="Cabinet name")
    description: Optional[str] = Field(default=None, description="Cabinet description")


# ==========================================
# ENTRY PAYLOADS (FILE / FOLDER)
# ==========================================


class CreateEntryPayload(DataModel):
    parent_path: ParentPath = Field(
        default="",
        description="Parent folder path. Leave empty if creating at the root of the cabinet.",
        examples=["", "Strategic_Plans/2026"],
    )
    name: EntryName = Field(
        ...,
        description="Name of the file or folder (without slashes)",
        examples=["Q1_Report.pdf", "Drafts"],
    )
    type: EntryTypeEnum = Field(
        ...,
        description="Entry type (e.g., folder, document, pdf, image)",
        examples=["pdf"],
    )
    size: Optional[int] = Field(
        default=None,
        ge=0,
        description="File size in bytes. MUST be null if type is 'folder'.",
        examples=[1048576],
    )
    mime_type: Optional[str] = Field(
        default=None,
        description="MIME type of the file. MUST be null if type is 'folder'.",
        examples=["application/pdf"],
    )
    author: Optional[str] = Field(
        default=None,
        description="Author or creator of the entry",
        examples=["John Doe"],
    )

    @model_validator(mode="after")
    def validate_logic_by_type(self):

        if self.type == EntryTypeEnum.FOLDER:
            if self.size is not None or self.mime_type is not None:
                raise ValueError(
                    "A folder cannot have 'size' or 'mime_type' attributes"
                )
        else:
            if self.size is None:
                raise ValueError(
                    f"A file of type '{self.type.value}' must have a 'size' attribute"
                )

        return self

    @property
    def computed_path(self) -> str:
        """Utility property to generate the absolute path for database storage."""
        if not self.parent_path:
            return self.name
        return f"{self.parent_path}/{self.name}"
