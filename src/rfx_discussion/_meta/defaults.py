from rfx_base import config as baseconf

LOG_LEVEL = baseconf.LOG_LEVEL
DB_DSN = baseconf.DB_DSN

RFX_DISCUSSION_SCHEMA = "cpo-discussion"
POLICY_SCHEMA = "cpo-policy"
POLICY_TABLE = "_policy--rfx-discussion"
COMMENT_NESTED_LEVEL = 2
NAMESPACE = "rfx-discussion"
MESSAGE_NAMESPACE = "rfx-message"
DEFAULT_TEAM_ID = None

PROJECT_MANAGEMENT_INTEGRATION_ENABLED = True
PROJECT_MANAGEMENT_INTEGRATION_PROVIDER = "linear"


# env for JIRA and CLICKUP integration
# JIRA_API_TOKEN = "xxx"
# JIRA_DOMAIN = "your-domain.atlassian.net"
# JIRA_PROJECT_KEY = "PROJ"

# CLICKUP_API_TOKEN = "xxx"
# CLICKUP_TEAM_ID = "xxx"
