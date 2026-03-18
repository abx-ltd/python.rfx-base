"""
RFX Document Type Definitions
=============================
Enums and type definitions for the document system.
"""

from enum import Enum

class EntryTypeEnum(str, Enum):
    FOLDER       = "FOLDER"
    DOCUMENT     = "DOCUMENT"
    IMAGE        = "IMAGE"
    VIDEO        = "VIDEO"
    AUDIO        = "AUDIO"
    PDF          = "PDF"
    SPREADSHEET  = "SPREADSHEET"
    PRESENTATION = "PRESENTATION"
