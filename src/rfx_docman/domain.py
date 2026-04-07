from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import RFXDocmanAggregate
from .state import RFXDocmanStateManager
from .policy import RFXDocmanPolicyManager, RFXDocmanPolicy  # noqa
from . import config


class RFXDocmanDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXDocmanAggregate
    __statemgr__ = RFXDocmanStateManager
    __logstore__ = SQLDomainLogStore
    __policymgr__ = RFXDocmanPolicyManager

class RealmResponse(RFXDocmanDomain.Response):
    pass
class RealmMetaResponse(RFXDocmanDomain.Response):
    pass
class ShelfResponse(RFXDocmanDomain.Response):
    pass
class CategoryResponse(RFXDocmanDomain.Response):
    pass
class CabinetResponse(RFXDocmanDomain.Response):
    pass
class EntryResponse(RFXDocmanDomain.Response):
    pass
class TagResponse(RFXDocmanDomain.Response):
    pass
class EntryTagResponse(RFXDocmanDomain.Response):
    pass