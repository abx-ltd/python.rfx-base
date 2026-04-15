from ._meta import config, logger
from fluvius.data import SqlaDriver

<<<<<<< HEAD

# # --- Base connector used by legacy tooling ---
# class RFXConnector(SqlaDriver):
#     __db_dsn__ = config.DB_DSN
#     __schema__ = config.DB_SCHEMA


# Domain-specific connectors (used by Alembic)
from .rfx_user import RFXUserConnector as IDMConnector
from .rfx_policy import RFXPolicyConnector
from .rfx_message import RFXMessageConnector
from .rfx_media import RFXMediaConnector
from .rfx_notify import RFXNotifyConnector
from .rfx_client import RFXClientConnector
from .rfx_discuss import RFXDiscussConnector
from .rfx_qr import RFXQRConnector
from .rfx_todo import RFXTodoConnector
from .rfx_template import RFXTemplateConnector
<<<<<<< HEAD
from .rfx_2dmessage import RFX2DMessageConnector
from .rfx_document import RFXDocumentConnector
=======
from .rfx_docman import RFXDocmanConnector
>>>>>>> 8935565 (refactor : docman)

DOMAIN_CONNECTORS = {
    "user": IDMConnector,
    "policy": RFXPolicyConnector,
    "message": RFXMessageConnector,
    "media": RFXMediaConnector,
    "notify": RFXNotifyConnector,
    "client": RFXClientConnector,
    "discuss": RFXDiscussConnector,
    "qr": RFXQRConnector,
    "todo": RFXTodoConnector,
    "template": RFXTemplateConnector,
<<<<<<< HEAD
    "2dmessage": RFX2DMessageConnector,
    "document": RFXDocumentConnector
=======
    "docman": RFXDocmanConnector,
>>>>>>> 8935565 (refactor : docman)
}
=======
# Domain connectors are now managed within their respective submodules
# to avoid circular imports.
>>>>>>> 06811eb (update: rfx schema)
