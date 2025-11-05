from datetime import datetime, timezone, timedelta
from fastapi import Request
from fluvius.data import UUID_TYPE, UUID_GENR
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import StringField, UUIDField, BooleanField, EnumField, PrimaryID

from .state import IDMStateManager
from .domain import UserProfileDomain
from .policy import UserProfilePolicyManager
from .types import InvitationStatusEnum


class UserProfileQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager
    # __policymgr__ = UserProfilePolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = UserProfileDomain.Meta.prefix
        tags = UserProfileDomain.Meta.tags


resource = UserProfileQueryManager.register_resource
endpoint = UserProfileQueryManager.register_endpoint


# @resource('user')
# class UserQuery(QueryResource):
#     """ List current user accounts """

#     class Meta(QueryResource.Meta):
#         include_all = True
#         allow_item_view = True
#         allow_list_view = False
#         allow_meta_view = False

#     _id = UUIDField("User ID", identifier=True)
#     name__given = StringField("Given Name")
#     name__family = StringField("Family Name")


# @endpoint('~active-profile/{profile_id}')
# async def my_profile(query: UserProfileQueryManager, request: Request, profile_id: str):
#     return f"ENDPOINT: {request} {query} {profile_id}"

@endpoint('.accept-invitation/{invitation_id}')
async def accept_invitation(query_manager: UserProfileQueryManager, request: Request, invitation_id: str):
    async with query_manager.data_manager.transaction():
        token = request.query_params.get('token')
        invitation = await query_manager.data_manager.fetch('invitation', invitation_id)
        context = request.state.auth_context
        if not invitation:
            return {"error": "Invitation not found"}
        if token != invitation.token:
            return {"error": "Invalid invitation token"}
        if invitation.user_id != context.profile.user_id:
            return {"error": "Invitation does not belong to the current user"}
        if invitation.status != InvitationStatusEnum.PENDING:
            return {"error": f"Invitation status is {invitation.status}, cannot accept"}
        existing_profile = await query_manager.data_manager.find_one('profile', where=dict(
            user_id=invitation.user_id,
            organization_id=invitation.organization_id
        ))
        if existing_profile:
            return {"error": "User already has a profile in this organization"}
        current_time = datetime.now(timezone(timedelta(hours=7)))
        if invitation.expires_at and invitation.expires_at < current_time:
            await query_manager.data_manager.update(invitation, status=InvitationStatusEnum.EXPIRED)
            invitation_status_record = dict(
                _id=UUID_GENR(),
                invitation_id=invitation._id,
                src_state=invitation.status,
                dst_state=invitation.status
            )
            await query_manager.data_manager.add_entry("invitation_status", **invitation_status_record)
            return {"error": "Invitation has expired"}

        await query_manager.data_manager.update(invitation, status=InvitationStatusEnum.ACCEPTED)

        invitation_status_record = dict(
            _id=UUID_GENR(),
            invitation_id=invitation._id,
            src_state=InvitationStatusEnum.ACCEPTED,
            dst_state=InvitationStatusEnum.ACCEPTED
        )
        await query_manager.data_manager.add_entry("invitation_status", **invitation_status_record)
        user = await query_manager.data_manager.fetch('user', context.profile.user_id)
        if not user:
            return {"error": "User not found"}
        profile_record = dict(
            _id=UUID_GENR(),
            organization_id=invitation.organization_id,
            user_id=user._id,
            name__family=user.name__family,
            name__given=user.name__given,
            name__middle=user.name__middle,
            name__prefix=user.name__prefix,
            name__suffix=user.name__suffix,
            telecom__email=user.telecom__email,
            telecom__phone=user.telecom__phone,
            status='ACTIVE',
            current_profile=False
        )
        await query_manager.data_manager.add_entry('profile', **profile_record)
        profile_status_record = dict(
            _id=UUID_GENR(),
            profile_id=profile_record['_id'],
            src_state=profile_record['status'],
            dst_state=profile_record['status']
        )
        await query_manager.data_manager.add_entry('profile_status', **profile_status_record)
        return {"success": True, "profile_id": str(profile_record['_id'])}

@endpoint('.reject-invitation/{invitation_id}')
async def reject_invitation(query_manager: UserProfileQueryManager, request: Request, invitation_id: str):
    async with query_manager.data_manager.transaction():
        token = request.query_params.get('token')
        invitation = await query_manager.data_manager.fetch('invitation', invitation_id)
        context = request.state.auth_context
        if not invitation:
            return {"error": "Invitation not found"}
        if token != invitation.token:
            return {"error": "Invalid invitation token"}
        if invitation.user_id != context.profile.user_id:
            return {"error": "Invitation does not belong to the current user"}
        if invitation.status != 'PENDING':
            return {"error": f"Invitation status is {invitation.status}, cannot reject"}
        await query_manager.data_manager.update(invitation, status='REJECTED')
        await query_manager.data_manager.add_entry(
            "invitation_status",
            _id=UUID_GENR(),
            invitation_id=invitation._id,
            src_state=invitation.status,
            dst_state=invitation.status
        )
        return {"success": True}



@resource('profile')
class ProfileQuery(DomainQueryResource):
    """ List current profile's user """
    class Meta(DomainQueryResource.Meta):
        allow_item_view = True
        allow_list_view = True

    @classmethod
    def base_query(cls, context, scope):
      return {'organization_id': context.organization._id}

    name__family: str = StringField("Family Name")
    name__given: str = StringField("Given Name")
    telecom__email: str = StringField("Email")
    status: str = StringField("Status")


class OrganizationRoleQuery(DomainQueryResource):
    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        resource = "organization"
        policy_required = "organization_id"

    user_id: UUID_TYPE = UUIDField("User ID")
    address__city: str = StringField("City")
    address__country: str = StringField("Country")
    address__line1: str = StringField("Address Line 1")
    address__line2: str = StringField("Address Line 2")
    address__postal: str = StringField("Postal Code")
    address__state: str = StringField("State/Province")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


@resource('profile-role')
class ProfileRole(DomainQueryResource):
    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        resource = "profile"
        policy_required = "profile_id"

    id: UUID_TYPE = PrimaryID("Profile ID")
    profile_id: str = StringField("Profile Id")
    role_key: str = StringField("Role Key")
    role_id: str = UUIDField("Role ID")
    role_source: str = StringField("Role Source")


@resource('organization')
class OrganizationQuery(DomainQueryResource):
    """ List current user's organizations """

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = False
        allow_meta_view = True

        resource = "organization"
        policy_required = "id"

    id: UUID_TYPE = PrimaryID("Organization ID")
    name: str = StringField("Organization name")
    description: str = StringField("Description")
    tax_id: str = StringField("Tax ID")
    business_name: str = StringField("Business Name")
    system_entity: str = BooleanField("System Entity")
    active: str = BooleanField("Active")
    system_tag: str = StringField("System Tag", array=True)
    user_tag: str = StringField("User Tag", array=True)
    organization_code: str = StringField("Organization Code")
    status: str = EnumField("Status")
    invitation_code: str = StringField("Invitation Code")
    type: str = StringField("Organization Type Key (ForeignKey)")
