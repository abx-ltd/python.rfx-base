from fluvius.domain import Domain, response
from fluvius.domain.logstore import SQLDomainLogStore

from .aggregate import IDMAggregate
from .state import IDMStateManager

from . import config


class IDMDomain(Domain):
	__domain__ = config.USER_MANAGEMENT_NAMESPACE
	__aggregate__ = IDMAggregate
	__statemgr__ = IDMStateManager
	__logstore__ = SQLDomainLogStore


_command = IDMDomain.command
_processor = IDMDomain.command_processor


class UserResponse(IDMDomain.Response):
	pass

class UserMessage(IDMDomain.Message):
    pass
