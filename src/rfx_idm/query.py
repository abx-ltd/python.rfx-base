from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Request
from pydantic import BaseModel
from fluvius.data import UUID_TYPE, UUID_GENR
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import StringField, UUIDField, BooleanField, EnumField, PrimaryID

from .state import IDMStateManager
from .domain import IDMDomain
from .policy import IDMPolicyManager
from .types import InvitationStatusEnum
from . import scope


class IDMQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager
    __policymgr__ = IDMPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = IDMDomain.Meta.prefix
        tags = IDMDomain.Meta.tags


resource = IDMQueryManager.register_resource
endpoint = IDMQueryManager.register_endpoint

@endpoint('.accept-invitation/{invitation_id}')
async def accept_invitation(query_manager: IDMQueryManager, request: Request, invitation_id: str):
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
        existing_profile = await query_manager.data_manager.exist('profile', where=dict(
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
async def reject_invitation(query_manager: IDMQueryManager, request: Request, invitation_id: str):
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

@resource('user')
class UserQuery(DomainQueryResource):
    """ List current user's basic info """

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "user"

        resource = "user"
        policy_required = "id"

    id: UUID_TYPE = PrimaryID("User ID")
    name__family: str = StringField("Family Name")
    name__given: str = StringField("Given Name")
    telecom__email: str = StringField("Email")
    telecom__phone: str = StringField("Phone")
    username: str = StringField("Username")
    verified_email: Optional[str] = StringField("Verified Email")
    verified_phone: Optional[str] = StringField("Verified Phone")
    is_super_admin: bool = BooleanField("Is Super Admin")
    status: str = StringField("Status")

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
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    telecom__email: str = StringField("Email")
    status: str = StringField("Status")

@resource('user-profile')
class UserProfileQuery(DomainQueryResource):
    """ List current profile's users """

    class Meta(DomainQueryResource.Meta):
        allow_item_view = False
        allow_list_view = True

        backend_model = "_profile_list"
        resource = "profile"
        policy_required = "id"
        scope_required = scope.ProfileListScopeSchema

    name__family: str = StringField("Family Name")
    name__given: str = StringField("Given Name")
    preferred_name: Optional[str] = StringField("Preferred Name")
    telecom__email: str = StringField("Email")
    telecom__phone: str = StringField("Phone")
    username: str = StringField("Username")
    user_id: UUID_TYPE = UUIDField("User ID")
    status: str = StringField("Status")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    user_id: UUID_TYPE = UUIDField("User ID")
    organization_name: str = StringField("Organization Name")


@resource('organization-member')
class ProfileListQuery(DomainQueryResource):
    """ List current profile's users """

    class Meta(DomainQueryResource.Meta):
        allow_item_view = False
        allow_list_view = True

        backend_model = "_org_member"
        resource = "profile"
        policy_required = "id"
        scope_required = scope.OrgProfileListScopeSchema

    name__family: str = StringField("Family Name")
    name__middle: Optional[str] = StringField("Middle Name")
    name__given: str = StringField("Given Name")
    telecom__email: str = StringField("Email")
    telecom__phone: str = StringField("Phone")

    user_id: UUID_TYPE = UUIDField("User ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    organization_name: str = StringField("Organization Name")
    profile_status: str = StringField("Status")
    profile_role: str = StringField("Role")
    policy_count: int = StringField("Policy Count")


@resource('profile-detail')
class ProfileDetailQuery(DomainQueryResource):
    """ List current profile's user """

    class Meta(DomainQueryResource.Meta):
        allow_item_view = True
        allow_list_view = False
        backend_model = "profile"

        resource = "profile"
        policy_required = "id"

    user_id: UUID_TYPE = UUIDField("User ID")
    name__family: str = StringField("Family Name")
    name__given: str = StringField("Given Name")
    telecom__email: str = StringField("Email")
    telecom__phone: str = StringField("Phone")
    status: str = StringField("Status")
    address__city: str = StringField("City")
    address__country: str = StringField("Country")
    address__line1: Optional[str] = StringField("Address Line 1")
    address__line2: Optional[str] = StringField("Address Line 2")
    address__postal: Optional[str] = StringField("Postal Code")
    address__state: Optional[str] = StringField("State/Province")
    picture_id: Optional[UUID_TYPE] = UUIDField("Picture ID")
    birthdate: Optional[datetime] = StringField("Birthdate")
    expiration_date: Optional[datetime] = StringField("Expiration DateTime")
    gender: Optional[str] = StringField("Gender")
    language: Optional[str] = StringField("Language", array=True)
    last_login: Optional[datetime] = StringField("Last Login")
    name__middle: Optional[str] = StringField("Middle Name")
    name__prefix: Optional[str] = StringField("Name Prefix")
    name__suffix: Optional[str] = StringField("Name Suffix")
    realm: Optional[str] = StringField("Realm")
    user_tag: Optional[str] = StringField("User Tag", array=True)
    telecom__fax: Optional[str] = StringField("Fax")
    two_factor_authentication: Optional[bool] = BooleanField("Two Factor Authentication")
    upstream_user_id: Optional[str] = StringField("Upstream User ID")
    user_type: Optional[str] = StringField("User Type")
    username: str = StringField("Username")
    verified_email: Optional[str] = StringField("Verified Email")
    verified_phone: Optional[str] = StringField("Verified Phone")
    primary_language: Optional[str] = StringField("Primary Language")
    last_sync: Optional[datetime] = StringField("Last Sync")
    npi: Optional[str] = StringField("NPI ID")
    verified_npi: Optional[bool] = BooleanField("Verified NPI")
    last_sync: Optional[datetime] = StringField("Last Sync")
    preferred_name: Optional[str] = StringField("Preferred Name")
    default_theme: Optional[str] = StringField("Default Theme")
    status: str = StringField("Profile Status")


@resource('profile-role')
class ProfileRole(DomainQueryResource):
    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "profile_role"

        resource = "profile"
        policy_required = "profile_id"
        scope_required = scope.ProfileRoleScopeSchema


    id: UUID_TYPE = PrimaryID("Profile ID")
    profile_id: str = StringField("Profile Id")
    role_key: str = StringField("Role Key")
    role_id: str = UUIDField("Role ID")
    role_source: str = StringField("Role Source")


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

@resource('organization')
class OrganizationDetailQuery(DomainQueryResource):
    """ Query organization details """

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "organization"

        resource = "organization"
        policy_required = "id"

    id: UUID_TYPE = PrimaryID("Organization ID")
    name: str = StringField("Organization name")
    description: str = StringField("Description")
    business_name: str = StringField("Business Name")
    system_entity: str = BooleanField("System Entity")
    active: str = BooleanField("Active")
    system_tag: str = StringField("System Tag", array=True)
    user_tag: str = StringField("User Tag", array=True)
    organization_code: str = StringField("Organization Code")
    status: str = EnumField("Status")
    invitation_code: str = StringField("Invitation Code")
    type: str = StringField("Organization Type Key (ForeignKey)")

@resource('sent-invitation')
class SentInvitationQuery(DomainQueryResource):
    """ List invitations for the current user's profiles """

    class Meta(DomainQueryResource.Meta):
        allow_item_view = True
        allow_list_view = True

        resource = "invitation"
        backend_model = "invitation"
        policy_required = "id"
        # scope_required = scope.SentInvitationScopeSchema


    id: UUID_TYPE = PrimaryID("Invitation ID")
    sender_id: UUID_TYPE = UUIDField("Sender User ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    user_id: UUID_TYPE = UUIDField("User ID")
    email: str = StringField("Email")
    status: str = EnumField("Status")
    message: str = StringField("Message")
    expires_at: datetime = StringField("Expiration DateTime")

@resource('received-invitation')
class ReceivedInvitationQuery(DomainQueryResource):
    """ List invitations received by the current user's profiles """

    class Meta(DomainQueryResource.Meta):
        allow_item_view = True
        allow_list_view = True

        backend_model = "invitation"
        resource = "invitation"
        policy_required = "id"

    id: UUID_TYPE = PrimaryID("Invitation ID")
    sender_id: UUID_TYPE = UUIDField("Sender User ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    user_id: UUID_TYPE = UUIDField("User ID")
    email: str = StringField("Email")
    status: str = EnumField("Status")
    message: str = StringField("Message")
    expires_at: datetime = StringField("Expiration DateTime")
