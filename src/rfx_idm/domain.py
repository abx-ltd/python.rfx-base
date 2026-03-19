from fluvius.domain import Domain, SQLDomainLogStore
from .aggregate import IDMAggregate
from .state import IDMStateManager
from .policy import IDMPolicyManager

from . import config


class IDMDomain(Domain):
	__namespace__ 	= config.IDM_NAMESPACE
	__aggregate__ 	= IDMAggregate
	__statemgr__ 	= IDMStateManager
	__logstore__ 	= SQLDomainLogStore
	__policymgr__   = IDMPolicyManager


class IDMResponse(IDMDomain.Response):
	pass


class IDMMessage(IDMDomain.Message):
    pass
