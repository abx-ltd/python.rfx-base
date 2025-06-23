from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import UserProfileAggregate
from .state import IDMStateManager
from .policy import UserProfilePolicyManager


class UserProfileDomain(Domain):
    __namespace__   = 'user-profile'
    __aggregate__   = UserProfileAggregate
    __statemgr__    = IDMStateManager
    __logstore__    = SQLDomainLogStore
    # __policymgr__   = UserProfilePolicyManager


class UserProfileResponse(UserProfileDomain.Response):
    pass


class UserProfileMessage(UserProfileDomain.Message):
    pass
