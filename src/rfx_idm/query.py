from fluvius.query import DomainQueryManager, QueryResource
from fluvius.query.field import StringField, PrimaryID
from uuid import UUID
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

    id: UUID = PrimaryID("User ID")
    name__given: str = StringField("Given Name")
    name__family: str = StringField("Family Name")


@IDMQueryManager.register_resource('organization')
class OrganizationQuery(QueryResource):
    """ List all organizations """

    id: UUID  = PrimaryID("Organization ID")
    name: str = StringField("Organization Name", description="Official name of the organization. E.g. One use in tax reports.")
    dba_name: str = StringField("Business Name", source="business_name", description="DBA (Doing-Business-As) Name")
