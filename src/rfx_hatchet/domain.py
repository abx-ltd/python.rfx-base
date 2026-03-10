from fluvius.domain import Domain, SQLDomainLogStore

from . import config
from .aggregate import RFXHatchetAggregate
from fluvius.hatchet.tracker import HatchetWorkflowTracker


class RFXHatchetDomain(Domain):
    """Domain for working with Hatchet workflow run tracking data."""

    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXHatchetAggregate
    __statemgr__ = HatchetWorkflowTracker
    __logstore__ = SQLDomainLogStore
