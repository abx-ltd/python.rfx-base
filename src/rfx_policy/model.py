
import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg

from . import config

class PolicyConnector(SqlaDriver):
    assert config.DB_DSN is not None, "DB_DSN must be set in config"

    __db_dsn__ = config.DB_DSN

# class PolicyBaseModel(PolicyConnector.__data_schema_base__, DomainSchema):
#     """
#     Base model for all IDM entities with schema qualification and realm support.
#     Provides common structure for multi-tenant operations with realm isolation.
#     """
#     __abstract__ = True
#     __table_args__ = {'schema': 'rfx--policy'}

#     _realm = sa.Column(sa.String)


# class PolicyEffectEnum(sa.Enum):
#     ALLOW = 'ALLOW'
#     DENY = 'DENY'

# class PolicyStatusEnum(sa.Enum):
#     ENABLED = 'ENABLED'
#     DISABLED = 'DISABLED'

# class PolicyScopeEnum(sa.Enum):
#     SYSTEM = 'SYSTEM'
#     PUBLIC = 'PUBLIC'

# class PolicyKindEnum(sa.Enum):
#     CUSTOM = 'CUSTOM'
#     SYSTEM = 'SYSTEM'
#     STATIC = 'STATIC'

# class PolicyCQRSEnum(sa.Enum):
#     COMMAND = 'COMMAND'
#     QUERY = 'QUERY'


# class Policy(PolicyBaseModel):
#     __tablename__ = 'policy'

#     key = sa.Column(sa.String)
#     display = sa.Column(sa.String)
#     description = sa.Column(sa.String)
#     priority = sa.Column(sa.Integer)
#     effect = sa.Column(sa.Enum(PolicyEffectEnum))
#     status = sa.Column(sa.Enum(PolicyStatusEnum))
#     scope = sa.Column(sa.Enum(PolicyScopeEnum))
#     kind = sa.Column(sa.Enum(PolicyKindEnum))


# class PolicyResource(PolicyBaseModel):
#     __tablename__ = 'policy_resource'

#     key = sa.Column(sa.String)
#     name = sa.Column(sa.String)
#     description = sa.Column(sa.String)
#     priority = sa.Column(sa.Integer)
#     effect = sa.Column(sa.Enum(PolicyEffectEnum))
#     status = sa.Column(sa.Enum(PolicyStatusEnum))
#     scope = sa.Column(sa.Enum(PolicyScopeEnum))
#     kind = sa.Column(sa.Enum(PolicyKindEnum))
#     cqrs = sa.Column(sa.Enum(PolicyCQRSEnum))
#     domain = sa.Column(sa.String)
#     action = sa.Column(sa.String)
#     resource = sa.Column(sa.String)
#     policy_key = sa.Column(sa.ForeignKey(Policy.key))
#     meta = sa.Column(sa.String)


# class PolicyRole(PolicyBaseModel):
#     __tablename__ = 'policy_role'

#     policy_key = sa.Column(sa.ForeignKey(Policy.key))
#     role_key = sa.Column(sa.String)
