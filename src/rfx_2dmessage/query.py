from .policy import RFX2DMessagePolicyManager
from .domain import RFX2DMessageDomain
from .state import RFX2DMessageStateManager
from fluvius.query import DomainQueryManager


class RFX2DMessageQueryManager(DomainQueryManager):
    __data_manager__ = RFX2DMessageStateManager
    __policymgr__ = RFX2DMessagePolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFX2DMessageDomain.Meta.namespace
        tags = RFX2DMessageDomain.Meta.tags


# Add query resources here as needed
# @RFX2DMessageQueryManager.register_resource("message")
# class MessageQuery(DomainQueryResource):
#     """Message queries"""