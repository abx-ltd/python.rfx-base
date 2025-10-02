""" Messaging domain """
from ._meta import config, logger

from .domain import MessageServiceDomain
from .query import MessageQueryManager
from . import command
