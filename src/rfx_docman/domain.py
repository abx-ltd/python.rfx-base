from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import RFXDocmanAggregate
from .state import RFXDocmanStateManager
from . import config


class RFXDocmanDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXDocmanAggregate
    __statemgr__ = RFXDocmanStateManager
    __logstore__ = SQLDomainLogStore


class DocmanResponse(RFXDocmanDomain.Response):
    pass
