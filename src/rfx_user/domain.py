from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import UserProfileAggregate
from .state import UserProfileStateManager

from . import config


class UserProfileDomain(Domain):
    __namespace__   = 'user-profile'
    __aggregate__   = UserProfileAggregate
    __statemgr__    = UserProfileStateManager
    __logstore__    = SQLDomainLogStore


class UserProfileResponse(UserProfileDomain.Response):
    pass


class UserProfileMessage(UserProfileDomain.Message):
    pass
