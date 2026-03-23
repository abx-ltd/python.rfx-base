from rfx_base import config as base_config
from rfx_schema import config as schema_config

LOG_LEVEL = base_config.LOG_LEVEL
DB_DSN = schema_config.RFX_MESSAGE_DB_DSN

MESSAGE_SERVICE_SCHEMA = "rfx_message"
POLICY_SCHEMA = "rfx_policy"
POLICY_TABLE = "_policy__user_profile"
NAMESPACE = "rfx-message"

WORKER_QUEUE_NAME = "rfx_worker"
