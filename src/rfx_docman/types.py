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

class RealmMetaKeyEnum(str, Enum):
    REALM = "REALM"
    SHELF = "SHELF"
    CATEGORY = "CATEGORY"
    CABINET = "CABINET"