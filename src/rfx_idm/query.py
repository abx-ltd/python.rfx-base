from fluvius.query import DomainQueryManager, DomainQueryResource
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
class UserQuery(DomainQueryResource):
    """ List all user accounts """
    class Meta:
        include_all = True

    id: UUID = PrimaryID("User ID")
    first_name: str = StringField("Given Name", source="name__given")
    name__family: str = StringField("Family Name")


@IDMQueryManager.register_resource('organization')
class OrganizationQuery(DomainQueryResource):
    """ List all organizations """
    class Meta:
        include_all = True

    id: UUID  = PrimaryID("Organization ID")
    name: str = StringField("Organization Name", description="Official name of the organization. E.g. One use in tax reports.")
    dba_name: str = StringField("Business Name", source="business_name", description="DBA (Doing-Business-As) Name")
