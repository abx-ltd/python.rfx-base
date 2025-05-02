from fluvius.query import DomainQueryManager
from .state import IDMStateManager
from .domain import IDMDomain


class IDMQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager

    class Meta:
        prefix = IDMDomain.__domain__
        tags = [IDMDomain.__name__]

