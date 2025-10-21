from rfx_base import config as baseconf

LOG_LEVEL = baseconf.LOG_LEVEL
DB_DSN = baseconf.DB_DSN

RFX_DISCUSSION_SCHEMA = "cpo-discussion"
POLICY_SCHEMA = "cpo-policy"
POLICY_TABLE = "_policy--rfx-discussion"
COMMENT_NESTED_LEVEL = 2
NAMESPACE = "rfx-discussion"
MESSAGE_NAMESPACE = "rfx-message"
UAPI_URL = "https://uapi.adaptive-bits.com/api/unified/proxy?api_key=69ENLxox1TkKm9nEP9AmdqWZ5xMUC7_QREOUBrXxd1A"
LINEAR_CONNECTION_ID = "d1f8831d-6808-4845-8db6-b8082fbb99e8"
DEFAULT_TEAM_ID = "a7fc113d-5b51-4f6e-8a82-18eccf73c71c"

PROJECT_MANAGEMENT_INTEGRATION_ENABLED = True
PROJECT_MANAGEMENT_INTEGRATION_PROVIDER = "linear" 
LINEAR_API_KEY = "69ENLxox1TkKm9nEP9AmdqWZ5xMUC7_QREOUBrXxd1A"
LINEAR_TEAM_ID = "a7fc113d-5b51-4f6e-8a82-18eccf73c71c"


# env for JIRA and CLICKUP integration
# JIRA_API_TOKEN = "xxx"
# JIRA_DOMAIN = "your-domain.atlassian.net"
# JIRA_PROJECT_KEY = "PROJ"

# CLICKUP_API_TOKEN = "xxx"
# CLICKUP_TEAM_ID = "xxx"