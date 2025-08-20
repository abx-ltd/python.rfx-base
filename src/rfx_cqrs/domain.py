from fluvius.domain import Domain
from fluvius.domain.logstore.sql import SQLDomainLogStore

from . import config
from .aggregate import RFXCqrsAggregate
from .state import RFXCqrsStateManager


class RFXCqrsDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXCqrsAggregate
    __statemgr__ = RFXCqrsStateManager
    __logstore__ = SQLDomainLogStore
