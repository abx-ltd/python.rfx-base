"""
Policy Domain Enum Definitions (Schema Layer)

These enums mirror the runtime definitions in ``src/rfx_policy/model.py`` so
that Alembic and the schema package can import them without loading the full
service stack.
"""

from enum import Enum


class PolicyEffectEnum(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class PolicyStatusEnum(Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class PolicyScopeEnum(Enum):
    SYSTEM   = "SYSTEM"
    TENANT   = "TENANT"
    RESOURCE = "RESOURCE"
    PUBLIC   = "PUBLIC"


class PolicyKindEnum(Enum):
    CUSTOM = "CUSTOM"
    SYSTEM = "SYSTEM"
    STATIC = "STATIC"


class PolicyCQRSEnum(Enum):
    COMMAND = "COMMAND"
    QUERY = "QUERY"
