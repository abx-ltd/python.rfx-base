from rfx_base import config as baseconf
from rfx_user import config as userconf

LOG_LEVEL = baseconf.LOG_LEVEL
DB_DSN = baseconf.DB_DSN
POLICY_SCHEMA = "rfx__user"
POLICY_TABLE = "_policy__idm_profile"

IDM_SCHEMA = "rfx__user"
IDM_NAMESPACE = "rfx-idm"
SERVICE_CLIENT = userconf.SERVICE_CLIENT

CHANGE_PASSWORD_PATH="/change-password"
