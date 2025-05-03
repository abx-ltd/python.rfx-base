from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import UserProfileAggregate
from .state import UserProfileStateManager

from . import config


class IDMDomain(Domain):
    __domain__      = config.IDM_NAMESPACE
    __aggregate__   = UserProfileAggregate
    __statemgr__    = UserProfileStateManager
    __logstore__    = SQLDomainLogStore


class UserProfileResponse(IDMDomain.Response):
    pass


class UserProfileMessage(IDMDomain.Message):
    pass
