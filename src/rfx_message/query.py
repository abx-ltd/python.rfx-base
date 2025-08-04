from fluvius.query import DomainQueryManager, DomainQueryResource

from .state import MessageStateManager
from .domain import MessageServiceDomain

class MessageQueryManager(DomainQueryManager):
    __data_manager__ = MessageStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = MessageServiceDomain.Meta.prefix
        tags = MessageServiceDomain.Meta.tags

resource = MessageQueryManager.register_resource
endpoint = MessageQueryManager.register_endpoint