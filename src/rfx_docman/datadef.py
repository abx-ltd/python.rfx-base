from typing import Optional, Protocol

from pydantic import Field, model_validator

from fluvius.data import DataModel, UUID_TYPE
from .types import EntryTypeEnum, RealmMetaKeyEnum
from .value_objects import (
    ShelfCode,
    CategoryCode,
    CabinetCode,
    EntryName,
    TagName,
    Path,
)


# --- Base payload ---


class BaseUpdatePayload(DataModel):
    """Requires at least one field to be provided."""

    @model_validator(mode="after")
    def at_least_one_field_required(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field is required to update")
        return self


# --- Realm ---


class CreateRealmPayload(DataModel):
    name: str = Field(..., description="Realm name", examples=["Corporate Hub"])
    description: Optional[str] = Field(default=None, description="Realm description")
    icon: Optional[str] = Field(
        default=None, description="Lucide icon identifier", examples=["building-2"]
    )
    color: Optional[str] = Field(
        default=None, description="Hex color code", examples=["#2563EB"]
    )


class UpdateRealmPayload(BaseUpdatePayload):
    name: Optional[str] = Field(default=None, description="Realm name")
    description: Optional[str] = Field(default=None, description="Realm description")
    icon: Optional[str] = Field(default=None, description="Lucide icon identifier")
    color: Optional[str] = Field(default=None, description="Hex color code")


# --- Realm Meta ---


class CreateRealmMetaPayload(DataModel):
    key: RealmMetaKeyEnum = Field(
        ..., description="Meta key", examples=["REALM", "SHELF", "CABINET"]
    )
    value: str = Field(
        ..., description="Meta value", examples=["Function", "Transaction"]
    )


class UpdateRealmMetaPayload(BaseUpdatePayload):
    key: Optional[RealmMetaKeyEnum] = Field(default=None, description="Meta key")
    value: Optional[str] = Field(default=None, description="Meta value")


# --- Shelf / Category / Cabinet ---


class CreateShelfPayload(DataModel):
    code: ShelfCode = Field(
        ..., description="Single uppercase letter", examples=["A"]
    )
    name: str = Field(
        ..., description="Shelf name", examples=["Governance & Management"]
    )
    description: Optional[str] = Field(default=None, description="Shelf description")


class UpdateShelfPayload(BaseUpdatePayload):
    code: Optional[ShelfCode] = Field(
        default=None, description="Single uppercase letter", examples=["B"]
    )
    name: Optional[str] = Field(default=None, description="Shelf name")
    description: Optional[str] = Field(default=None, description="Shelf description")


class CreateCategoryPayload(DataModel):
    code: CategoryCode = Field(
        ..., description="Category code (Shelf prefix + 2 digits)", examples=["A01"]
    )
    name: str = Field(..., description="Category name", examples=["Strategic Planning"])
    description: Optional[str] = Field(
        default=None, description="Category description"
    )


class UpdateCategoryPayload(BaseUpdatePayload):
    code: Optional[CategoryCode] = Field(
        default=None,
        description="Category code (Shelf prefix + 2 digits)",
        examples=["A02"],
    )
    name: Optional[str] = Field(default=None, description="Category name")
    description: Optional[str] = Field(
        default=None, description="Category description"
    )


class CreateCabinetPayload(DataModel):
    code: CabinetCode = Field(
        ..., description="Cabinet code (Category prefix + 3 digits)", examples=["A01-001"]
    )
    name: str = Field(..., description="Cabinet name", examples=["Annual Reports 2026"])
    description: Optional[str] = Field(default=None, description="Cabinet description")


class UpdateCabinetPayload(BaseUpdatePayload):
    code: Optional[CabinetCode] = Field(
        default=None,
        description="Cabinet code (Category prefix + 3 digits)",
        examples=["A01-002"],
    )
    name: Optional[str] = Field(default=None, description="Cabinet name")
    description: Optional[str] = Field(default=None, description="Cabinet description")


# --- Entry (file / folder) ---


class _EntryLike(Protocol):
    """Minimal interface expected of an entry domain object."""
    path: str
    name: str


class CreateEntryPayload(DataModel):
    parent_path: Path = Field(
        default="",
        description="Parent folder path. Empty = root of cabinet.",
        examples=["", "Strategic_Plans/2026"],
    )
    name: EntryName = Field(
        ...,
        description="File or folder name (no slashes)",
        examples=["Q1_Report.pdf", "Drafts"],
    )
    type: EntryTypeEnum = Field(
        ...,
        description="Entry type: folder, document, pdf, image, ...",
        examples=["PDF"],
    )
    size: Optional[int] = Field(
        default=None,
        ge=0,
        description="File size in bytes. Must be null for folders.",
        examples=[1048576],
    )
    mime_type: Optional[str] = Field(
        default=None,
        description="MIME type. Must be null for folders.",
        examples=["application/pdf"],
    )
    author_name: Optional[str] = Field(
        default=None,
        description="Author name",
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
        """Absolute path for DB storage."""
        return str(self.parent_path.join(str(self.name)))


class UpdateEntryPayload(BaseUpdatePayload):
    parent_path: Optional[Path] = Field(
        default=None, description="New parent path (move entry)."
    )
    name: Optional[EntryName] = Field(
        default=None, description="New name."
    )
    type: Optional[EntryTypeEnum] = Field(
        default=None, description="New entry type."
    )
    size: Optional[int] = Field(default=None, ge=0)
    mime_type: Optional[str] = Field(default=None, description="New MIME type.")
    author_name: Optional[str] = Field(default=None, description="Author name.")

    @model_validator(mode="after")
    def validate_type_consistency(self):
        if self.type is None:
            return self
        if self.type == EntryTypeEnum.FOLDER:
            if self.size is not None or self.mime_type is not None:
                raise ValueError(
                    "A folder cannot have 'size' or 'mime_type' attributes"
                )
        return self

    def resolve_path(self, entry: _EntryLike) -> str:
        """Resolve the new absolute path given the current entry state."""
        current = Path.from_string(str(entry.path))
        parent = self.parent_path if self.parent_path is not None else current.parent()
        name = str(self.name) if self.name is not None else str(entry.name)
        return str(parent.join(name))


# --- Tag ---


class CreateTagPayload(DataModel):
    name: TagName = Field(..., description="Tag name", examples=["urgent", "archived"])
    color: Optional[str] = Field(
        default=None, description="Hex color code", examples=["#EF4444"]
    )
    icon: Optional[str] = Field(
        default=None, description="Lucide icon name", examples=["tag"]
    )


class UpdateTagPayload(BaseUpdatePayload):
    name: Optional[TagName] = Field(default=None, description="Tag name")
    color: Optional[str] = Field(default=None, description="Hex color code")
    icon: Optional[str] = Field(default=None, description="Lucide icon name")


# --- Entry Tag ---


class AddEntryTagPayload(DataModel):
    tag_id: UUID_TYPE = Field(..., description="Tag ID to attach")


class RemoveEntryTagPayload(DataModel):
    tag_id: UUID_TYPE = Field(..., description="Tag ID to detach")
