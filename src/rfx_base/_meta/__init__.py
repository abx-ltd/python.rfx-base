from fluvius import setupModule
from . import defaults

config, logger = setupModule(__name__, defaults)

# Fallback to default service client if specific clients are not set
config.MESSAGE_CLIENT = config.MESSAGE_CLIENT or config.DEFAULT_SERVICE_CLIENT
config.NOTIFY_CLIENT = config.NOTIFY_CLIENT or config.DEFAULT_SERVICE_CLIENT
config.TEMPLATE_CLIENT = config.TEMPLATE_CLIENT or config.DEFAULT_SERVICE_CLIENT
