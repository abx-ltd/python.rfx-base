from fluvius.query import DomainQueryManager

from ..state import MessageStateManager
from ..domain import RFXMessageServiceDomain
from .. import scope  # noqa


class RFXMessageServiceQueryManager(DomainQueryManager):
    __data_manager__ = MessageStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXMessageServiceDomain.Meta.namespace
        tags = RFXMessageServiceDomain.Meta.tags


resource = RFXMessageServiceQueryManager.register_resource
endpoint = RFXMessageServiceQueryManager.register_endpoint
