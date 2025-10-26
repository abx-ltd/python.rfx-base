"""
RFX User Domain Type Definitions

Enum classes defining status values and source classifications used throughout
the RFX User domain for consistent state management and data validation.
"""

from enum import Enum


class OrganizationStatusEnum(Enum):
    """Organization lifecycle status values."""
    ACTIVE      = "ACTIVE"      # Organization is operational and accepting members
    INACTIVE    = "INACTIVE"    # Organization is temporarily disabled
    SETUP       = "SETUP"       # Organization is being configured (initial state)
    REVIEW      = "REVIEW"      # Organization pending administrative approval
    DEACTIVATED = "DEACTIVATED" # Organization permanently disabled


class ProfileStatusEnum(Enum):
    """User profile status within organization context."""
    ACTIVE                   = "ACTIVE"                   # Profile is active and has access
    INACTIVE                 = "INACTIVE"                 # Profile temporarily disabled
    EXPIRED                  = "EXPIRED"                  # Profile access has expired
    PENDING                  = "PENDING"                  # Profile awaiting activation
    DEACTIVATED              = "DEACTIVATED"              # Profile permanently disabled
    ORGANIZATION_DEACTIVATED = "ORGANIZATION_DEACTIVATED" # Disabled due to organization status


class UserSourceEnum(Enum):
    """Source system or method of user authentication."""
    WEB       = "WEB"       # Web browser authentication
    MOBILE    = "MOBILE"    # Mobile app direct authentication
    KEYCLOAK  = "KEYCLOAK"  # Keycloak SSO authentication
    MOBILE_KC = "MOBILE_KC" # Mobile app via Keycloak


class UserStatusEnum(Enum):
    """User account status across the system."""
    ACTIVE      = "ACTIVE"      # User account is active and accessible
    INACTIVE    = "INACTIVE"    # User account temporarily disabled
    EXPIRED     = "EXPIRED"     # User account has expired
    PENDING     = "PENDING"     # User account awaiting activation
    DEACTIVATED = "DEACTIVATED" # User account permanently disabled


class InvitationStatusEnum(Enum):
    """Organization invitation workflow status."""
    PENDING  = "PENDING"  # Invitation sent, awaiting response
    ACCEPTED = "ACCEPTED" # Invitation accepted by user
    EXPIRED  = "EXPIRED"  # Invitation expired before acceptance
    REVOKED  = "REVOKED"  # Invitation cancelled by sender


class UserActionStatusEnum(str, Enum):
    """Status of required user actions (e.g., password reset, email verification)."""
    PENDING   = 'PENDING'   # Action required, not yet completed
    COMPLETED = 'COMPLETED' # Action successfully completed
