""" Notification domain """
from ._meta import config, logger

from .domain import NotifyServiceDomain
from .query import NotifyServiceQueryManager
from . import command
