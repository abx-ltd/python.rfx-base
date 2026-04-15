from rfx_base import config as baseconf
from rfx_user import config as userconf

LOG_LEVEL = baseconf.LOG_LEVEL
DB_DSN = None
POLICY_SCHEMA = "rfx__user"
POLICY_TABLE = "_policy__idm_profile"

IDM_SCHEMA = "rfx__user"
IDM_NAMESPACE = "rfx-idm"
NOTIFY_NAMESPACE = "rfx-notify"
NOTIFY_CLIENT = baseconf.NOTIFY_CLIENT

CHANGE_PASSWORD_PATH="/change-password"
ALLOW_CREATE_SYS_ADMIN = False
SYSTEM_ORGANIZATION_ID = None
OPERATION_VALID_REALMS = userconf.OPERATION_VALID_REALMS
