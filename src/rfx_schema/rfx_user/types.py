"""
RFX User Domain Type Definitions (Schema Layer)

This is a re-export of types from rfx_user.types to avoid circular imports
and database initialization issues when Alembic loads the schema modules.

By importing directly from this module, we bypass the rfx_user package __init__
which triggers domain/state/model initialization requiring DB configuration.
"""

from enum import Enum


class OrganizationStatusEnum(Enum):
    """Organization lifecycle status values."""
    ACTIVE      = "ACTIVE"
    INACTIVE    = "INACTIVE"
    SETUP       = "SETUP"
    REVIEW      = "REVIEW"
    DEACTIVATED = "DEACTIVATED"
    NEW         = "NEW"


class ProfileStatusEnum(Enum):
    """User profile status within organization context."""
    ACTIVE                   = "ACTIVE"
    INACTIVE                 = "INACTIVE"
    EXPIRED                  = "EXPIRED"
    PENDING                  = "PENDING"
    DEACTIVATED              = "DEACTIVATED"
    ORGANIZATION_DEACTIVATED = "ORGANIZATION_DEACTIVATED"


class UserSourceEnum(Enum):
    """Source system or method of user authentication."""
    WEB       = "WEB"
    MOBILE    = "MOBILE"
    KEYCLOAK  = "KEYCLOAK"
    MOBILE_KC = "MOBILE_KC"


class UserStatusEnum(Enum):
    """User account status across the system."""
    ACTIVE      = "ACTIVE"
    INACTIVE    = "INACTIVE"
    EXPIRED     = "EXPIRED"
    PENDING     = "PENDING"
    DEACTIVATED = "DEACTIVATED"
    NEW         = "NEW"


class InvitationStatusEnum(Enum):
    """Organization invitation workflow status."""
    PENDING  = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED  = "EXPIRED"
    REJECTED = "REJECTED"


class UserActionStatusEnum(Enum):
    """Status of user required actions."""
    PENDING    = "PENDING"
    COMPLETED  = "COMPLETED"
    CANCELLED  = "CANCELLED"

class UserActionTypeEnum(Enum):
    """Types of user actions."""
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
