"""
RFX Todo Type Definitions
=============================
Enums and type definitions for the todo system.
"""

from enum import Enum  # noqa: F401


class TodoStatusEnum(Enum):
    NEW = "NEW"
    DONE = "DONE"
