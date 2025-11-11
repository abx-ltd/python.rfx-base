from rfx_base import config

LOG_LEVEL = config.LOG_LEVEL
DB_DSN = config.DB_DSN

NOTIFY_SERVICE_SCHEMA = "rfx_notify"
POLICY_SCHEMA = "rfx_policy"
POLICY_TABLE = "_policy__user_profile"
NAMESPACE = "rfx-notify"

# ============================================================================
# SELF-HOSTED INFRASTRUCTURE CONFIGURATION
# Email and SMS are sent through services running on the worker machine
# ============================================================================

# Self-hosted SMTP Server Configuration
# The SMTP server (Postfix, Haraka, etc.) runs on the worker machine
SMTP_HOST = "localhost"  # Worker's SMTP server
SMTP_PORT = 25  # Standard SMTP port (use 587 for TLS, 465 for SSL)
SMTP_USE_TLS = False  # Set True if using port 587
SMTP_USE_SSL = False  # Set True if using port 465
SMTP_USERNAME = None  # Set if SMTP server requires authentication
SMTP_PASSWORD = None  # Set if SMTP server requires authentication
SMTP_FROM_EMAIL = "noreply@yourdomain.com"  # Default sender email
SMTP_TIMEOUT = 30  # Connection timeout in seconds

# Self-hosted Kannel SMS Gateway Configuration
# Kannel SMS gateway runs on the worker machine
KANNEL_HOST = "localhost"  # Worker's Kannel server
KANNEL_PORT = 13013  # Kannel HTTP admin interface port
KANNEL_USERNAME = "admin"  # Kannel admin username
KANNEL_PASSWORD = "admin"  # Kannel admin password
KANNEL_FROM_NUMBER = None  # Default SMS sender number (if applicable)
KANNEL_SEND_URL = "/cgi-bin/sendsms"  # Kannel send SMS endpoint
KANNEL_DLR_MASK = 31  # Delivery report mask (31 = all reports)
KANNEL_TIMEOUT = 30  # Connection timeout in seconds

# Rate Limiting Configuration
NOTIFY_RATE_LIMIT_PER_MINUTE = 60
NOTIFY_RATE_LIMIT_PER_HOUR = 1000
NOTIFY_RATE_LIMIT_PER_DAY = 10000


