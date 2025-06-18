from fastapi import Request
from typing import Optional
from fluvius.query import DomainQueryManager, QueryResource, endpoint
<<<<<<< HEAD
from fastapi import Request
from fluvius.query.field import StringField, PrimaryID
=======
from fluvius.query.field import StringField, UUIDField, BooleanField, EnumField
from fluvius.data import UUID_TYPE
>>>>>>> 699659a85ea312e4260e4a987dce023ad188b6a9

from .state import IDMStateManager
from .domain import UserProfileDomain
from .policy import UserProfilePolicyManager
from .types import OrganizationStatus

class UserProfileQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager
    __policymgr__ = UserProfilePolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = UserProfileDomain.Meta.prefix
        tags = UserProfileDomain.Meta.tags


resource = UserProfileQueryManager.register_resource
endpoint = UserProfileQueryManager.register_endpoint


# @resource('user')
# class UserQuery(QueryResource):
#     """ List current user accounts """

#     class Meta(QueryResource.Meta):
#         select_all = True
#         allow_item_view = True
#         allow_list_view = False
#         allow_meta_view = False

#     _id = UUIDField("User ID", identifier=True)
#     name__given = StringField("Given Name")
#     name__family = StringField("Family Name")


# @endpoint('~active-profile/{profile_id}')
# async def my_profile(query: UserProfileQueryManager, request: Request, profile_id: str):
#     return f"ENDPOINT: {request} {query} {profile_id}"


@resource('profile')
class ProfileQuery(QueryResource):
    """ List current profile's user """

    id: str  = PrimaryID("Organization ID", identifier=True)
    name: str = StringField("Organization Name")



@resource('organization')
class OrganizationQuery(QueryResource):
    """ List current user's organizations """

    id: str  = PrimaryID("Organization ID", identifier=True)
    name: str = StringField("Organization Name")
    dba_name: str = StringField("Business Name", source="business_name")


class OrganizationRoleQuery(QueryResource):
    class Meta(QueryResource.Meta):
        select_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        scope_required = {
            "resource": str,
            "resource_id": str
        }
        policy_required = True

    id = PrimaryID("Profile ID", identifier=True)
    user_id  = UUIDField("User ID")
    address__city = StringField("City")
    address__country = StringField("Country")
    address__line1 = StringField("Address Line 1")
    address__line2 = StringField("Address Line 2")
    address__postal = StringField("Postal Code")
    address__state = StringField("State/Province")


@resource('profile-role')
class ProfileRole(QueryResource):
    class Meta(QueryResource.Meta):
        select_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        scope_required = {
            "resource": str,
            "resource_id": UUID_TYPE
        }
        policy_required = True

    id = PrimaryID("Profile ID", identifier=True)
    profile_id = StringField("Profile Id")
    role_key = StringField("Role Key")
    role_id = UUIDField("Role ID")
    role_source = StringField("Role Source")


@resource('organization')
class OrganizationQuery(QueryResource):
    """ List current user's organizations """

    class Meta(QueryResource.Meta):
        select_all = True
        allow_item_view = True
        allow_list_view = False
        allow_meta_view = True

        policy_required = True
        scope_required = {"resource": str, "resource_id": str}

    id = PrimaryID("Organization ID", identifier=True)
    name: str = StringField("Organization name")
    description: str = StringField("Description")
    tax_id: str = StringField("Tax ID")
    business_name: str = StringField("Business Name")
    system_entity: str = BooleanField("System Entity")
    active: str = BooleanField("Active")
    system_tag: str = StringField("System Tag", array=True)
    user_tag: str = StringField("User Tag", array=True)
    organization_code: str = StringField("Organization Code")
    status: str = EnumField("Status", enum=OrganizationStatus)
    invitation_code: str = StringField("Invitation Code")
    type: str = StringField("Organization Type Key (ForeignKey)")
