from rfx_base import config as base_config
from rfx_schema import config as schema_config

LOG_LEVEL = base_config.LOG_LEVEL
DB_DSN = schema_config.RFX_DISCUSS_DB_DSN

RFX_DISCUSS_SCHEMA = "rfx_discuss"
POLICY_SCHEMA = None
RFX_USER_SCHEMA = base_config.RFX_USER_SCHEMA

MESSAGE_NAMESPACE = "rfx-message"

POLICY_TABLE = "_policy__rfx_discuss"
COMMENT_NESTED_LEVEL = 2

NAMESPACE = "rfx-discuss"
MESSAGE_NAMESPACE = "rfx-message"

MESSAGE_ENABLED = True

WEBHOOK_SECRET = "SECRET"
CALLBACK_URL = "URL"