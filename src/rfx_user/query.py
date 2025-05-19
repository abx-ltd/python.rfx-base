from typing import Optional
from fluvius.query import DomainQueryManager, QueryResource, endpoint
from fluvius.query.field import StringField, UUIDField
from fastapi import Request
from .state import IDMStateManager
from .domain import UserProfileDomain

class UserProfileQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager

    class Meta(DomainQueryManager.Meta):
        api_prefix = UserProfileDomain.Meta.api_prefix
        api_tags = UserProfileDomain.Meta.api_tags


resource = UserProfileQueryManager.register_resource
endpoint = UserProfileQueryManager.register_endpoint


@resource('user')
class UserQuery(QueryResource):
    """ List current user accounts """

    class Meta(QueryResource.Meta):
        select_all = True
        allow_item_view = False
        allow_list_view = False
        allow_meta_view = False

    _id = UUIDField("User ID", identifier=True)
    name__given = StringField("Given Name")
    name__family = StringField("Family Name")


@endpoint('active-profile/{profile_id}')
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

