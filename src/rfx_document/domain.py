from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import RFXDocumentAggregate
from .state import RFXDocumentStateManager
from . import config

class RFXDocumentDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXDocumentAggregate
    __statemgr__ = RFXDocumentStateManager
    __logstore__ = SQLDomainLogStore


class DocumentResponse(RFXDocumentDomain.Response):
    pass
