from rfx_base import config

LOG_LEVEL = config.LOG_LEVEL
DB_DSN = config.DB_DSN

MESSAGE_SERVICE_SCHEMA = "rfx_message"
POLICY_SCHEMA = "rfx_policy"
POLICY_TABLE = "_policy__user_profile"
NAMESPACE = "rfx-message"

WORKER_QUEUE_NAME = "cpo_portal_worker"