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
    build_entry_path,
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
    code: ShelfCode = Field(..., description="Single uppercase letter", examples=["A"])
    name: str = Field(
        ..., description="Shelf name", examples=["Governance & Management"]
    )
    description: Optional[str] = Field(default=None, description="Shelf description")


class UpdateShelfPayload(BaseUpdatePayload):
    name: Optional[str] = Field(default=None, description="Shelf name")
    description: Optional[str] = Field(default=None, description="Shelf description")


class CreateCategoryPayload(DataModel):
    code: CategoryCode = Field(
        ..., description="Category code (Shelf prefix + 2 digits)", examples=["A01"]
    )
    name: str = Field(..., description="Category name", examples=["Strategic Planning"])
    description: Optional[str] = Field(default=None, description="Category description")


class UpdateCategoryPayload(BaseUpdatePayload):
    name: Optional[str] = Field(default=None, description="Category name")
    description: Optional[str] = Field(default=None, description="Category description")


class CreateCabinetPayload(DataModel):
    code: CabinetCode = Field(
        ...,
        description="Cabinet code (Category prefix + 3 digits)",
        examples=["A01-001"],
    )
    name: str = Field(..., description="Cabinet name", examples=["Annual Reports 2026"])
    description: Optional[str] = Field(default=None, description="Cabinet description")


class UpdateCabinetPayload(BaseUpdatePayload):
    name: Optional[str] = Field(default=None, description="Cabinet name")
    description: Optional[str] = Field(default=None, description="Cabinet description")


# --- Entry (file / folder) ---
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
    media_entry_id: Optional[UUID_TYPE] = Field(
        default=None,
        description="ID returned by media upload API. Required for all types except FOLDER.",
        examples=["3c012cc7-54a6-423a-b226-085623c09898"],
    )

    @model_validator(mode="after")
    def validate_logic_by_type(self):
        if self.type == EntryTypeEnum.FOLDER:
            if self.media_entry_id is not None:
                raise ValueError("FOLDER cannot have media_entry_id.")
        else:
            if self.media_entry_id is None:
                raise ValueError(f"type={self.type.value} requires media_entry_id.")
        return self


class _EntryLike(Protocol):
    """Minimal interface expected of an entry domain object."""

    parent_path: str
    name: str


class UpdateEntryPayload(BaseUpdatePayload):
    parent_path: Optional[Path] = Field(
        default=None, description="New parent path (move entry)."
    )
    name: Optional[EntryName] = Field(default=None, description="New name.")

    def resolve_path(self, entry: _EntryLike) -> str:
        """Resolve the new absolute path given the current entry state."""
        current_parent = Path.from_string(str(entry.parent_path))
        parent = self.parent_path if self.parent_path is not None else current_parent
        name = str(self.name) if self.name is not None else str(entry.name)
        return build_entry_path(parent, name)


class CopyEntryPayload(DataModel):
    cabinet_id: UUID_TYPE = Field(..., description="Cabinet ID to copy into")
    parent_path: Path = Field(
        ...,
        description="Parent folder path in the destination cabinet. Empty = root.",
        examples=["", "Strategic_Plans/2026"],
    )
    name: Optional[EntryName] = Field(
        default=None,
        description="New name for the copied entry (no slashes). If not provided, original name will be used.",
        examples=["Q1_Report_Copy.pdf"],
    )


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
