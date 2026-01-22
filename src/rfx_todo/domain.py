from fluvius.domain import Domain, SQLDomainLogStore

from .aggregate import RFXTodoAggregate
from .state import RFXTodoStateManager
from .policy import RFXTodoPolicyManager
from . import config


class RFXTodoDomain(Domain):
    __namespace__ = config.NAMESPACE
    __aggregate__ = RFXTodoAggregate
    __statemgr__ = RFXTodoStateManager
    __logstore__ = SQLDomainLogStore
    __policymgr__ = RFXTodoPolicyManager


class TodoResponse(RFXTodoDomain.Response):
    pass
