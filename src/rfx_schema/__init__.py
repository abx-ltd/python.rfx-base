from ._meta import config, logger
from fluvius.data import SqlaDriver


# # --- Base connector used by legacy tooling ---
# class RFXConnector(SqlaDriver):
#     __db_dsn__ = config.DB_DSN
#     __schema__ = config.DB_SCHEMA


# Domain-specific connectors (used by Alembic)
from .rfx_user import RFXUserConnector
from .rfx_policy import RFXPolicyConnector
from .rfx_message import RFXMessageConnector
from .rfx_media import RFXMediaConnector
from .rfx_notify import RFXNotifyConnector
from .rfx_client import RFXClientConnector
from .rfx_discuss import RFXDiscussConnector

DOMAIN_CONNECTORS = {
    "user": RFXUserConnector,
    "policy": RFXPolicyConnector,
    "message": RFXMessageConnector,
    "media": RFXMediaConnector,
    "notify": RFXNotifyConnector,
    "client": RFXClientConnector,
    "discuss": RFXDiscussConnector,
}
