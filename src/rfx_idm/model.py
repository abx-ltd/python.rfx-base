import sqlalchemy as sa

from fluvius.data import SqlaDataSchema, SqlaDriver, UUID_GENR
from sqlalchemy.dialects import postgresql as pg

from . import types, config


class IDMConnector(SqlaDriver):
	__db_dsn__ = config.DB_DSN


class IDMBaseModel(SqlaDataSchema):
    __abstract__ = True
    __table_args__ = {'schema': config.IDM_SCHEMA}

    _id = sa.Column(pg.UUID, primary_key=True, nullable=False, default=UUID_GENR, server_default=sa.text("uuid_generate_v1()"))
    _created = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"))
    _updated = sa.Column(sa.DateTime(timezone=True), nullable=True)
    _creator = sa.Column(pg.UUID, default=UUID_GENR)
    _updater = sa.Column(pg.UUID, nullable=True)
    _deleted = sa.Column(sa.DateTime(timezone=True))
    _etag = sa.Column(sa.String)

    def __init_subclass__(cls):
        cls._register_with_driver(IDMConnector)


class RefAction(IDMBaseModel):
    __tablename__ = "ref--action"

    key = sa.Column(sa.String(1024), nullable=False, unique=True)
    display = sa.Column(sa.String(1024), nullable=True)


class RefOrganizationType(IDMBaseModel):
    __tablename__ = "ref--organization-type"

    key = sa.Column(sa.String, nullable=False, unique=True)
    display = sa.Column(sa.String, nullable=True)


class RefRealm(IDMBaseModel):
    __tablename__ = "ref--realm"

    key = sa.Column(sa.String, nullable=False, unique=True)
    display = sa.Column(sa.String, nullable=True)


class RefRoleType(IDMBaseModel):
    __tablename__ = "ref--role-type"

    key = sa.Column(sa.String, nullable=False, unique=True)
    display = sa.Column(sa.String, nullable=True)


class RefSystemRole(IDMBaseModel):
    __tablename__ = "ref--system-role"

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


class UserSchema(IDMBaseModel):
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
    status = sa.Column(sa.Enum(types.UserStatus), nullable=False)


class UserIdentity(IDMBaseModel):
    __tablename__ = "user-identity"

    provider = sa.Column(sa.String, nullable=False)
    provider_user_id = sa.Column(sa.String, nullable=False)
    active = sa.Column(sa.Boolean)
    telecom__email = sa.Column(sa.String)
    telecom__phone = sa.Column(sa.String)

    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=False)


class UserSession(IDMBaseModel):
    __tablename__ = "user-session"

    source = sa.Column(sa.Enum(types.UserSource), nullable=True)
    telecom__email = sa.Column(sa.String)
    user_id = sa.Column(sa.ForeignKey(UserSchema._id))
    user_identity_id = sa.Column(sa.ForeignKey(UserIdentity._id))


class UserStatus(IDMBaseModel):
    __tablename__ = "user-status"

    status = sa.Column(sa.Enum(types.UserStatus), nullable=False)
    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=False)


class UserVerification(IDMBaseModel):
    __tablename__ = "user-verification"

    verification = sa.Column(sa.String(1024), nullable=False)
    last_sent_email = sa.Column(sa.DateTime(timezone=True))

    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=False)
    user_identity_id = sa.Column(sa.ForeignKey(UserIdentity._id))


class UserAction(IDMBaseModel):
    __tablename__ = "user-action"

    _iid = sa.Column(pg.UUID)
    action = sa.Column(sa.ForeignKey(RefAction.key))
    name = sa.Column(sa.String(1024))

    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=False)
    user_identity_id = sa.Column(sa.ForeignKey(UserIdentity._id))


class Organization(IDMBaseModel):
    __tablename__ = "organization"

    description = sa.Column(sa.String)
    name = sa.Column(sa.String(255))
    group_npi = sa.Column(sa.String(10))
    tax_id = sa.Column(sa.String(9))
    business_name = sa.Column(sa.String(255))
    system_entity = sa.Column(sa.Boolean)
    active = sa.Column(sa.Boolean)
    default_signer_id = sa.Column(pg.UUID)
    verified_tax_id = sa.Column(sa.String(255))
    verified_npi = sa.Column(sa.String(255))
    system_tag = sa.Column(pg.ARRAY(sa.String))
    user_tag = sa.Column(pg.ARRAY(sa.String))
    organization_code = sa.Column(sa.String(255))

    status = sa.Column(sa.Enum(types.OrganizationStatus), nullable=False)

    invitation_code = sa.Column(sa.String(10))
    type = sa.Column(sa.ForeignKey(RefOrganizationType.key))


class OrganizationDelegatedAccess(IDMBaseModel):
    __tablename__ = "organization-delegated-access"

    organization_id = sa.Column(sa.ForeignKey(Organization._id))
    delegated_organization_id = sa.Column(sa.ForeignKey(Organization._id))
    access_scope = sa.Column(sa.String)



class OrganizationRole(IDMBaseModel):
    __tablename__ = "organization-role"

    _iid = sa.Column(pg.UUID)
    _txt = sa.Column(pg.TSVECTOR)
    active = sa.Column(sa.Boolean)
    description = sa.Column(sa.String(1024))
    name = sa.Column(sa.String(1024))
    key = sa.Column(sa.String(255))
    organization_id = sa.Column(sa.ForeignKey(Organization._id))
    is_system_owner = sa.Column(sa.Boolean)
    is_system_signer = sa.Column(sa.Boolean)


class OrganizationStatus(IDMBaseModel):
    __tablename__ = "organization-status"

    organization_id = sa.Column(sa.ForeignKey(Organization._id))
    status = sa.Column(sa.Enum(types.OrganizationStatus), nullable=False)


class Profile(IDMBaseModel):
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
    status = sa.Column(sa.Enum(types.ProfileStatus), nullable=False)

    preferred_name = sa.Column(sa.String(255))
    default_theme = sa.Column(sa.String(255))

    user_id = sa.Column(sa.ForeignKey(UserSchema._id), nullable=True)
    current_profile = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("false"))
    organization_id = sa.Column(sa.ForeignKey(Organization._id), nullable=True)


class ProfileLocation(IDMBaseModel):
    __tablename__ = "profile-location"

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
    __tablename__ = "profile-status"

    status = sa.Column(sa.Enum(types.ProfileStatus), nullable=False)
    profile_id = sa.Column(sa.ForeignKey(Profile._id), nullable=False)


class OrganizationMember(IDMBaseModel):
    __tablename__ = "organization-member"

    member_id = sa.Column(sa.ForeignKey(Profile._id))
    organization_id = sa.Column(sa.ForeignKey(Organization._id))
    role_key = sa.Column(sa.String(255))
    role_id = sa.Column(pg.UUID)
    _source_id = sa.Column(sa.Integer)


class Group(IDMBaseModel):
    __tablename__ = "group"

    _txt = sa.Column(pg.TSVECTOR)
    description = sa.Column(sa.String(1024))
    name = sa.Column(sa.String(1024))
    resource = sa.Column(sa.String)
    resource_id = sa.Column(pg.UUID)


class GroupMember(IDMBaseModel):
    __tablename__ = "group-member"

    group_id = sa.Column(pg.UUID, sa.ForeignKey(Group._id))
    profile_id = sa.Column(pg.UUID, sa.ForeignKey(Profile._id))
