from enum import Enum


class OrganizationStatus(Enum):
    ACTIVE   = "ACTIVE"
    INACTIVE = "INACTIVE"
    SETUP    = "SETUP"
    REVIEW   = "REVIEW"


class ProfileStatus(Enum):
    ACTIVE                   = "ACTIVE"
    INACTIVE                 = "INACTIVE"
    EXPIRED                  = "EXPIRED"
    PENDING                  = "PENDING"
    DEACTIVATED              = "DEACTIVATED"
    ORGANIZATION_DEACTIVATED = "ORGANIZATION_DEACTIVATED"


class UserSource(Enum):
    WEB       = "WEB"
    MOBILE    = "MOBILE"
    KEYCLOAK  = "KEYCLOAK"
    MOBILE_KC = "MOBILE_KC"


class UserStatus(Enum):
    ACTIVE   = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED  = "EXPIRED"
    PENDING  = "PENDING"
