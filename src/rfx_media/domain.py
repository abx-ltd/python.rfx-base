from fluvius.domain import Domain, SQLDomainLogStore
from fluvius.media import MediaManager

from . import config
from .aggregate import RFXMediaAggregate


class RFXMediaDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXMediaAggregate
    __statemgr__ = MediaManager
    __logstore__ = SQLDomainLogStore
