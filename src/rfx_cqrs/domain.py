from fluvius.domain import Domain, SQLDomainLogStore

from . import config
from .state import RFXCqrsStateManager
from .aggregate import RFXCqrsAggregate


class RFXCqrsDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXCqrsAggregate
    __statemgr__ = RFXCqrsStateManager
    __logstore__ = SQLDomainLogStore
