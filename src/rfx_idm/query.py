from fluvius.query import DomainQueryManager, QuerySchema
from fluvius.query.field import StringField, UUIDField
from .state import IDMStateManager
from .domain import IDMDomain


class IDMQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager

    class Meta:
        api_prefix = IDMDomain.Meta.api_prefix
        api_tags = IDMDomain.Meta.api_tags


@IDMQueryManager.register_schema('user')
class UserQuery(QuerySchema):
    _id = UUIDField("User ID", identifier=True)
    name__given = StringField("Given Name")
    name__family = StringField("Family Name")


@IDMQueryManager.register_schema('organization')
class OrganizationiQuery(QuerySchema):
    _id = UUIDField("Organization ID", identifier=True)
    name = StringField("Organization Name")
