from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import UserProfileAggregate
from .state import IDMStateManager


class UserProfileDomain(Domain):
    __namespace__   = 'user-profile'
    __aggregate__   = UserProfileAggregate
    __statemgr__    = IDMStateManager
    __logstore__    = SQLDomainLogStore


class UserProfileResponse(UserProfileDomain.Response):
    pass


class UserProfileMessage(UserProfileDomain.Message):
    pass
