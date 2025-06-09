from typing import Optional
from fluvius.query import DomainQueryManager, QueryResource, endpoint
from fastapi import Request
from fluvius.query.field import StringField, UUIDField

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

    _id = UUIDField("User ID", identifier=True)
    name__given = StringField("Given Name")
    name__family = StringField("Family Name")


@endpoint('~active-profile/{profile_id}')
async def my_profile(query: UserProfileQueryManager, request: Request, profile_id: str):
    return f"ENDPOINT: {request} {query} {profile_id}"


@resource('profile')
class ProfileQuery(QueryResource):
    """ List current user's organizations """

    _id  = UUIDField("Organization ID", identifier=True)
    name = StringField("Organization Name")



@resource('organization')
class OrganizationQuery(QueryResource):
    """ List current user's organizations """

    _id  = UUIDField("Organization ID", identifier=True)
    name = StringField("Organization Name")
    dba_name = StringField("Business Name", source="business_name")


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

    _id  = UUIDField("Organization ID", identifier=True)
    name = StringField("Name")
    description = StringField("Description")
