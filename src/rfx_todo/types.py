"""
RFX Todo Type Definitions
=============================
Enums and type definitions for the todo system.
"""

# Currently no custom enums needed for todo.
from enum import Enum


class TodoStatusEnum(str, Enum):
    NEW = "NEW"
    DONE = "DONE"
