""" Messaging domain """
from ._meta import config, logger

from .domain import RFXMessageServiceDomain
from .query import RFXMessageServiceQueryManager
from . import command
