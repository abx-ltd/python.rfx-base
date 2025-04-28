from fluvius.domain import Domain, response
from fluvius.domain.logstore import SQLDomainLogStore

from .aggregate import UserAggregate
from .state import UserStateManager

from user_management import config


class UserDomain(Domain):
	__domain__ = config.USER_DOMAIN_NAMESPACE
	__aggregate__ = UserAggregate
	__statemgr__ = UserStateManager
	__logstore__ = SQLDomainLogStore


_entity = UserDomain.entity
_command = UserDomain.command
_processor = UserDomain.command_processor


@_entity
class UserResponse(response.DomainResponse):
	pass
