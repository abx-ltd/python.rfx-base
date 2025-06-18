from typing import Optional
from fluvius.query import DomainQueryManager, QueryResource, endpoint
from fastapi import Request
from fluvius.query.field import StringField, PrimaryID

from .state import IDMStateManager
from .domain import UserProfileDomain

class UserProfileQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = UserProfileDomain.Meta.prefix
        tags = UserProfileDomain.Meta.tags


resource = UserProfileQueryManager.register_resource
endpoint = UserProfileQueryManager.register_endpoint


@resource('user')
class UserQuery(QueryResource):
    """ List current user accounts """

    class Meta(QueryResource.Meta):
        select_all = True
        allow_item_view = True
        allow_list_view = False
        allow_meta_view = False

    id: str = PrimaryID("User ID")
    name__given: str = StringField("Given Name")
    name__family: str = StringField("Family Name")


@endpoint('~active-profile/{profile_id}')
async def my_profile(query: UserProfileQueryManager, request: Request, profile_id: str):
    return f"ENDPOINT: {request} {query} {profile_id}"


@resource('profile')
class ProfileQuery(QueryResource):
    """ List current user's organizations """

    id: str  = PrimaryID("Organization ID", identifier=True)
    name: str = StringField("Organization Name")



@resource('organization')
class OrganizationQuery(QueryResource):
    """ List current user's organizations """

    id: str  = PrimaryID("Organization ID", identifier=True)
    name: str = StringField("Organization Name")
    dba_name: str = StringField("Business Name", source="business_name")


@resource('organization-role')
class OrganizationRoleQuery(QueryResource):
    class Meta(QueryResource.Meta):
        backend_model = "organization-role"
        select_all = True
        allow_item_view = False
        allow_list_view = True
        allow_meta_view = True

        scope_required = {
            "resource": str,
            "resource_id": str
        }

    id: str  = PrimaryID("Organization ID", identifier=True)
    name: str = StringField("Name")
    description: str = StringField("Description")
