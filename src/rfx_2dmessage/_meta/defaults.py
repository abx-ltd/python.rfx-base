from rfx_base import config

LOG_LEVEL = config.LOG_LEVEL
DB_DSN = config.DB_DSN

RFX_2DMESSAGE_SERVICE_SCHEMA = "rfx_2dmessage"
POLICY_SCHEMA = "rfx_policy"
POLICY_TABLE = "_policy__rfx_2dmessage"
NAMESPACE = "rfx-2dmessage"

WORKER_QUEUE_NAME = "rfx_worker"