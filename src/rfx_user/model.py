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
from rfx_schema import RFXUserConnector

from . import types, config

class IDMConnector(SqlaDriver):
    """Database connection driver for Identity and Access Management schema."""
    assert config.DB_DSN, "[rfx_user.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN
    __schema__ = config.USER_PROFILE_SCHEMA
