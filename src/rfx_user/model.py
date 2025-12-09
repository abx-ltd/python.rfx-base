"""
RFX User Domain SQLAlchemy Data Models

Comprehensive data model definitions for multi-tenant identity and access management system.
Implements PostgreSQL-backed persistence layer with enum support, foreign key relationships,
and audit trail capabilities through the Fluvius domain framework.

Model Categories:
- Reference Tables: Static lookup data for actions, roles, organization types
- User Models: Core user identity, authentication, and session management
- Organization Models: Multi-tenant organizational structure and custom roles
- Profile Models: User profiles within organizational contexts with RBAC
- Invitation Models: Secure organization invitation workflow with status tracking
- Group Models: Security groups for permissions and access control

Database Features:
- PostgreSQL ENUM types for status values with schema qualification
- Full-text search support via TSVECTOR columns
- JSON columns for flexible role and access data storage
- UUID primary keys with foreign key relationships
- Timezone-aware datetime fields for audit trails
- Array columns for tag-based categorization

Integration Points:
- Fluvius DomainSchema base class for event sourcing
- SqlaDriver for database connection management
- Schema-qualified enums matching domain types
- Audit trail tables for status change tracking
"""

import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg

from . import types, config


class IDMConnector(SqlaDriver):
    """Database connection driver for Identity and Access Management schema."""
    assert config.DB_DSN, "[rfx_user.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN

class IDMBaseModel(IDMConnector.__data_schema_base__, DomainSchema):
    """
    Base model for all IDM entities with schema qualification and realm support.
    Provides common structure for multi-tenant operations with realm isolation.
    """
    __abstract__ = True
    __table_args__ = {'schema': config.USER_PROFILE_SCHEMA}

    _realm = sa.Column(sa.String)


# ==========================================================================
# REFERENCE TABLES
# Static lookup data for system operations and classifications
# ==========================================================================

class RefAction(IDMBaseModel):
    """Reference table for user actions that can be tracked and audited."""
    __tablename__ = "ref__action"

    key = sa.Column(sa.String(1024), nullable=False, unique=True)
    display = sa.Column(sa.String(1024), nullable=True)


class RefOrganizationType(IDMBaseModel):
    """Reference table for organization type classifications (e.g., healthcare, business)."""
    __tablename__ = "ref__organization_type"

    key = sa.Column(sa.String, nullable=False, unique=True)
    display = sa.Column(sa.String, nullable=True)


class RefRealm(IDMBaseModel):
    """Reference table for authentication realms in multi-tenant system."""
    __tablename__ = "ref__realm"

    key = sa.Column(sa.String, nullable=False, unique=True)
    display = sa.Column(sa.String, nullable=True)


class RefRoleType(IDMBaseModel):
    """Reference table for role type classifications (system, organization, custom)."""
    __tablename__ = "ref__role_type"

    key = sa.Column(sa.String, nullable=False, unique=True)
    display = sa.Column(sa.String, nullable=True)


class RefSystemRole(IDMBaseModel):
    """
    System-wide role definitions with priority and default assignments.
    Defines roles that span across organizations with specific capabilities.
    """
    __tablename__ = "ref__system_role"

    description = sa.Column(sa.String(1024))
    name = sa.Column(sa.String(1024), nullable=False)
    key = sa.Column(sa.String(255))
    active = sa.Column(sa.Boolean)
    is_owner = sa.Column(sa.Boolean)
    is_default_signer = sa.Column(sa.Boolean)
    default_role = sa.Column(sa.Boolean)
    official_role = sa.Column(sa.Boolean)
    priority = sa.Column(sa.Integer)
    role_type = sa.Column(sa.ForeignKey(RefRoleType.key), nullable=True)


# ==========================================================================
# USER MODELS
# Core user identity, authentication, and session management
# ==========================================================================

class UserSchema(IDMBaseModel):
    """
    Primary user entity with identity information and Keycloak integration.
    Stores user profile data, authentication status, and role access mappings.
    """
    __tablename__ = "user"

    active = sa.Column(sa.Boolean)

    # Name fields
    name__family = sa.Column(sa.String(1024))
    name__given = sa.Column(sa.String(1024))
    name__middle = sa.Column(sa.String(1024))
    name__prefix = sa.Column(sa.String(1024))
    name__suffix = sa.Column(sa.String(1024))

    # Telecom
    telecom__email = sa.Column(sa.String(1024))
    telecom__phone = sa.Column(sa.String(1024))

    # Identity
    username = sa.Column(sa.String(1024))
    verified_email = sa.Column(sa.String(1024))
    verified_phone = sa.Column(sa.String(1024))
    is_super_admin = sa.Column(sa.Boolean, default=False)

    # Enum: user_status (from PostgreSQL ENUM type)
    status = sa.Column(
        sa.Enum(types.UserStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    realm_access = sa.Column(sa.JSON)
    resource_access = sa.Column(sa.JSON)

    last_verified_request = sa.Column(sa.DateTime(timezone=True))


class UserIdentity(IDMBaseModel):
    """
    External identity provider linkages for federated authentication.
    Links users to external providers like social login or enterprise SSO.
    """
    __tablename__ = "user_identity"

    provider = sa.Column(sa.String, nullable=False)
    provider_user_id = sa.Column(sa.String, nullable=False)
    active = sa.Column(sa.Boolean)
    telecom__email = sa.Column(sa.String)
    telecom__phone = sa.Column(sa.String)

    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=False)


class UserSession(IDMBaseModel):
    """
    User session tracking for authentication and activity monitoring.
    Links sessions to users and identity providers for audit trails.
    """
    __tablename__ = "user_session"

    source = sa.Column(sa.Enum(types.UserSourceEnum), nullable=True)
    telecom__email = sa.Column(sa.String)
    user_id = sa.Column(sa.ForeignKey(UserSchema._id))
    user_identity_id = sa.Column(sa.ForeignKey(UserIdentity._id))


class UserStatus(IDMBaseModel):
    """
    Audit trail for user status changes with source and destination states.
    Tracks user lifecycle transitions for compliance and debugging.
    """
    __tablename__ = "user_status"

    src_state = sa.Column(
        sa.Enum(types.UserStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    dst_state = sa.Column(
        sa.Enum(types.UserStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=False)
    note = sa.Column(sa.String)


class UserVerification(IDMBaseModel):
    """
    Email and phone verification tracking with timestamp history.
    Manages verification codes and tracks verification request frequency.
    """
    __tablename__ = "user_verification"

    verification = sa.Column(sa.String(1024), nullable=False)
    last_sent_email = sa.Column(sa.DateTime(timezone=True))

    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=False)
    user_identity_id = sa.Column(sa.ForeignKey(UserIdentity._id))


class UserAction(IDMBaseModel):
    """
    User action tracking with status monitoring for Keycloak actions.
    Records actions sent to users and tracks completion status.
    """
    __tablename__ = "user_action"

    _iid = sa.Column(pg.UUID)
    action = sa.Column(sa.ForeignKey(RefAction.key))
    name = sa.Column(sa.String(1024))
    status = sa.Column(
        sa.Enum(types.UserActionStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False,
        server_default=types.UserActionStatusEnum.PENDING.value
    )

    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=False)
    user_identity_id = sa.Column(sa.ForeignKey(UserIdentity._id))


# ==========================================================================
# ORGANIZATION MODELS
# Multi-tenant organizational structure and custom roles
# ==========================================================================

class Organization(IDMBaseModel):
    """
    Multi-tenant organization entity with business information and configuration.
    Central entity for organizational boundaries and custom role definitions.
    """
    __tablename__ = "organization"

    description = sa.Column(sa.String)
    name = sa.Column(sa.String(255))
    # gov_id = sa.Column(sa.String(10))  # government issued id
    tax_id = sa.Column(sa.String(9))   # tax authority issued id
    business_name = sa.Column(sa.String(255))
    system_entity = sa.Column(sa.Boolean)
    active = sa.Column(sa.Boolean)
    system_tag = sa.Column(pg.ARRAY(sa.String))
    user_tag = sa.Column(pg.ARRAY(sa.String))
    organization_code = sa.Column(sa.String(255))

    status = sa.Column(
        sa.Enum(types.OrganizationStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )

    invitation_code = sa.Column(sa.String(10))
    type = sa.Column(sa.ForeignKey(RefOrganizationType.key))

    # Additional contact and profile fields from ttp_organization
    contact_person = sa.Column(sa.String)
    contact_email = sa.Column(sa.String)
    contact_phone = sa.Column(sa.String)
    address = sa.Column(sa.String)
    vat_number = sa.Column(sa.String)
    registered_date = sa.Column(sa.DateTime)
    avatar = sa.Column(sa.String)


class OrganizationDelegatedAccess(IDMBaseModel):
    """
    Cross-organizational access delegation for shared resources.
    Enables organizations to grant limited access to other organizations.
    """
    __tablename__ = "organization_delegated_access"

    organization_id = sa.Column(sa.ForeignKey(Organization._id))
    delegated_organization_id = sa.Column(sa.ForeignKey(Organization._id))
    access_scope = sa.Column(sa.String)


class OrganizationRole(IDMBaseModel):
    """
    Custom roles defined within organizational scope with full-text search.
    Allows organizations to create specialized roles beyond system defaults.
    """
    __tablename__ = "organization_role"

    _iid = sa.Column(pg.UUID)
    _txt = sa.Column(pg.TSVECTOR)
    active = sa.Column(sa.Boolean)
    description = sa.Column(sa.String(1024))
    name = sa.Column(sa.String(1024))
    key = sa.Column(sa.String(255))
    organization_id = sa.Column(sa.ForeignKey(Organization._id))


class OrganizationStatus(IDMBaseModel):
    """
    Audit trail for organization status changes with transition tracking.
    Records organizational lifecycle events for compliance and history.
    """
    __tablename__ = "organization_status"

    organization_id = sa.Column(sa.ForeignKey(Organization._id))
    src_state = sa.Column(
        sa.Enum(types.OrganizationStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    dst_state = sa.Column(
        sa.Enum(types.OrganizationStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    note = sa.Column(sa.String())


# ==========================================================================
# PROFILE MODELS
# User profiles within organizational contexts with RBAC
# ==========================================================================

class Profile(IDMBaseModel):
    """
    User profile within organizational context with comprehensive identity data.
    Links users to organizations with role-based access control and preferences.
    Supports multi-factor authentication, location tracking, and service access.
    """
    __tablename__ = "profile"

    access_tags = sa.Column(pg.ARRAY(sa.String))
    active = sa.Column(sa.Boolean)

    address__city = sa.Column(sa.String(1024))
    address__country = sa.Column(sa.String(1024))
    address__line1 = sa.Column(sa.String(1024))
    address__line2 = sa.Column(sa.String(1024))
    address__postal = sa.Column(sa.String(1024))
    address__state = sa.Column(sa.String(1024))

    picture_id = sa.Column(pg.UUID)
    birthdate = sa.Column(sa.DateTime(timezone=True))
    expiration_date = sa.Column(sa.DateTime(timezone=True))
    gender = sa.Column(sa.String(1024))

    language = sa.Column(pg.ARRAY(sa.String))
    last_login = sa.Column(sa.DateTime(timezone=True))

    name__family = sa.Column(sa.String(1024))
    name__given = sa.Column(sa.String(1024))
    name__middle = sa.Column(sa.String(1024))
    name__prefix = sa.Column(sa.String(1024))
    name__suffix = sa.Column(sa.String(1024))

    realm = sa.Column(sa.String(1024))
    svc_access = sa.Column(sa.String(1024))
    svc_secret = sa.Column(sa.String(1024))
    user_tag = sa.Column(pg.ARRAY(sa.String))

    telecom__email = sa.Column(sa.String(1024))
    telecom__fax = sa.Column(sa.String(1024))
    telecom__phone = sa.Column(sa.String(1024))

    tfa_method = sa.Column(sa.String(1024))
    tfa_token = sa.Column(sa.String(1024))
    two_factor_authentication = sa.Column(sa.Boolean)

    upstream_user_id = sa.Column(pg.UUID)
    user_type = sa.Column(sa.String(1024))
    username = sa.Column(sa.String(1024))

    verified_email = sa.Column(sa.String(1024))
    verified_phone = sa.Column(sa.String(1024))
    primary_language = sa.Column(sa.String(255))
    npi = sa.Column(sa.String(255))
    verified_npi = sa.Column(sa.String(255))

    last_sync = sa.Column(sa.DateTime(timezone=True))
    is_super_admin = sa.Column(sa.Boolean)
    system_tag = sa.Column(pg.ARRAY(sa.String))
    status = sa.Column(
        sa.Enum(types.ProfileStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    preferred_name = sa.Column(sa.String(255))
    default_theme = sa.Column(sa.String(255))

    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=True)
    current_profile = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("false"))
    organization_id = sa.Column(sa.ForeignKey(Organization._id), nullable=True)


class ProfileLocation(IDMBaseModel):
    """
    Geographic and device tracking for profile security and analytics.
    Records device information and location data for session management.
    """
    __tablename__ = "profile_location"

    _iid = sa.Column(pg.UUID)
    profile_id = sa.Column(sa.ForeignKey(Profile._id), nullable=False)
    app_name = sa.Column(sa.String(255))
    app_version = sa.Column(sa.String(15))
    device_id = sa.Column(sa.String(255))
    device_type = sa.Column(sa.String(255))
    ip_address = sa.Column(sa.String(15))
    lat = sa.Column(sa.Float)
    lng = sa.Column(sa.Float)


class ProfileStatus(IDMBaseModel):
    """
    Audit trail for profile status transitions within organizations.
    Tracks profile lifecycle changes with notes for compliance.
    """
    __tablename__ = "profile_status"
    src_state = sa.Column(
        sa.Enum(types.ProfileStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    dst_state = sa.Column(
        sa.Enum(types.ProfileStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    note = sa.Column(sa.String())
    profile_id = sa.Column(sa.ForeignKey(Profile._id), nullable=False)


class ProfileRole(IDMBaseModel):
    """
    Role assignments linking profiles to system or organizational roles.
    Supports multiple role sources for flexible permission management.
    """
    __tablename__ = "profile_role"

    profile_id = sa.Column(sa.ForeignKey(Profile._id))
    role_key = sa.Column(sa.String(255))
    role_id = sa.Column(pg.UUID)
    role_source = sa.Column(sa.String(255))


# ==========================================================================
# GROUP MODELS
# Security groups for permissions and access control
# ==========================================================================

class Group(IDMBaseModel):
    """
    Security groups for organizing profiles with shared permissions.
    Supports full-text search and resource-scoped group definitions.
    """
    __tablename__ = "group"

    _txt = sa.Column(pg.TSVECTOR)
    description = sa.Column(sa.String(1024))
    name = sa.Column(sa.String(1024))
    resource = sa.Column(sa.String)
    resource_id = sa.Column(pg.UUID)

class ProfileGroup(IDMBaseModel):
    """
    Many-to-many relationship linking profiles to security groups.
    Enables group-based permission management and access control.
    """
    __tablename__ = "profile_group"

    group_id = sa.Column(pg.UUID, sa.ForeignKey(Group._id))
    profile_id = sa.Column(pg.UUID, sa.ForeignKey(Profile._id))


# ==========================================================================
# INVITATION MODELS
# Secure organization invitation workflow with status tracking
# ==========================================================================

class Invitation(IDMBaseModel):
    """
    Organization invitation with secure token and expiration management.
    Handles invitation lifecycle from creation to acceptance/rejection.
    """
    __tablename__ = "invitation"

    organization_id = sa.Column(pg.UUID, sa.ForeignKey(Organization._id))
    sender_id = sa.Column(pg.UUID, sa.ForeignKey(UserSchema._id), nullable=False)
    profile_id = sa.Column(pg.UUID, sa.ForeignKey(Profile._id), nullable=True)
    user_id = sa.Column(pg.UUID, sa.ForeignKey(UserSchema._id))
    email = sa.Column(sa.String)
    token = sa.Column(sa.String)
    status = sa.Column(
        sa.Enum(types.InvitationStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    expires_at = sa.Column(sa.DateTime(timezone=True))
    message = sa.Column(sa.String)
    duration = sa.Column(sa.Integer)


class InvitationStatus(IDMBaseModel):
    """
    Audit trail for invitation status changes with transition tracking.
    Records invitation lifecycle events for security and compliance.
    """
    __tablename__ = "invitation_status"

    invitation_id = sa.Column(pg.UUID, sa.ForeignKey(Invitation._id))
    src_state = sa.Column(
        sa.Enum(types.InvitationStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    dst_state = sa.Column(
        sa.Enum(types.InvitationStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    note = sa.Column(sa.String)


class ProfileListView(IDMConnector.__data_schema_base__, DomainSchema):
    """
    Database view for listing user profiles with key identity fields.
    Provides a read-only view optimized for profile listing operations.
    """
    __tablename__ = "_profile_list"
    __table_args__ = {'schema': config.USER_PROFILE_SCHEMA}
    __view__ = True

    organization_id = sa.Column(pg.UUID)
    organization_name = sa.Column(sa.String)
    user_id = sa.Column(pg.UUID)
    username = sa.Column(sa.String)
    name__given = sa.Column(sa.String)
    name__family = sa.Column(sa.String)
    preferred_name = sa.Column(sa.String)
    active = sa.Column(sa.Boolean)
    status = sa.Column(
        sa.Enum(types.ProfileStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )


class OrgMemberView(IDMConnector.__data_schema_base__, DomainSchema):
    """
    Database view for organization members with profile and role details.
    Provides a read-only view optimized for organization member queries.
    """
    __tablename__ = "_org_member"
    __table_args__ = {'schema': config.USER_PROFILE_SCHEMA}
    __view__ = True

    profile_id = sa.Column(pg.UUID)
    user_id = sa.Column(pg.UUID)
    organization_id = sa.Column(pg.UUID)
    organization_name = sa.Column(sa.String)
    name__given = sa.Column(sa.String)
    name__middle = sa.Column(sa.String)
    name__family = sa.Column(sa.String)
    telecom__email = sa.Column(sa.String)
    telecom__phone = sa.Column(sa.String)
    profile_status = sa.Column(
        sa.Enum(types.ProfileStatusEnum, schema=config.USER_PROFILE_SCHEMA),
        nullable=False
    )
    profile_role = sa.Column(sa.String)
    policy_count = sa.Column(sa.Integer)

