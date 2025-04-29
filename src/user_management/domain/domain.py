from fluvius.domain import Domain, response
from fluvius.domain.logstore import SQLDomainLogStore

from .aggregate import UserManagementAggregate
from .state import UserManagementStateManager

from user_management import config


class UserManagementDomain(Domain):
	__domain__ = config.USER_MANAGEMENT_NAMESPACE
	__aggregate__ = UserManagementAggregate
	__statemgr__ = UserManagementStateManager
	__logstore__ = SQLDomainLogStore


_command = UserManagementDomain.command
_processor = UserManagementDomain.command_processor


class UserResponse(UserManagementDomain.Response):
	pass

class UserMessage(UserManagementDomain.Message):
    pass
