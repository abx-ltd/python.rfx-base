from fluvius.query import DomainQueryManager, QueryResource
from fluvius.query.field import StringField, UUIDField
from .state import IDMStateManager
from .domain import IDMDomain


class IDMQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager

    class Meta:
        prefix = IDMDomain.Meta.prefix
        tags = IDMDomain.Meta.tags


@IDMQueryManager.register_resource('user')
class UserQuery(QueryResource):
    """ List all user accounts """
    class Meta:
        select_all = True

    _id = UUIDField("User ID", identifier=True)
    name__given = StringField("Given Name")
    name__family = StringField("Family Name")


@IDMQueryManager.register_resource('organization')
class OrganizationQuery(QueryResource):
    """ List all organizations """

    _id  = UUIDField("Organization ID", identifier=True)
    name = StringField("Organization Name")
    dba_name = StringField("Business Name", source="business_name")
