"""
RFX Docman Type Definitions
=============================
Enums and type definitions for the docman system.
"""

from enum import Enum


class EntryTypeEnum(str, Enum):
    FOLDER = "FOLDER"

    DOCUMENT = "DOCUMENT"  # Word, RTF
    PDF = "PDF"
    SPREADSHEET = "SPREADSHEET"  # Excel, CSV
    PRESENTATION = "PRESENTATION"  # PowerPoint
    TEXT = "TEXT"  # TXT, Markdown
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    ARCHIVE = "ARCHIVE"  # ZIP, RAR
    CODE = "CODE"  # .py, .js, .sql

    OTHER = "OTHER"

    @property
    def is_folder(self) -> bool:
        return self == self.FOLDER

    def validate_entry_fields(self, size: int | None, mime_type: str | None) -> None:
        if self.is_folder:
            if size is not None or mime_type is not None:
                raise ValueError(
                    "A folder cannot have 'size' or 'mime_type' attributes"
                )
        else:
            if size is None:
                raise ValueError(
                    f"A file of type '{self.value}' must have a 'size' attribute"
                )
            if mime_type is None :
                raise ValueError(
                    f"A file of type '{self.value}' must have a 'mime_type' attribute"
                )
            


class RealmMetaKeyEnum(str, Enum):
    REALM = "REALM"
    SHELF = "SHELF"
    CATEGORY = "CATEGORY"
    CABINET = "CABINET"
