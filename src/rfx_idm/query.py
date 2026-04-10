from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import quote
from fastapi import Request
from fluvius.data import UUID_TYPE, UUID_GENR
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import (
    StringField,
    UUIDField,
    BooleanField,
    EnumField,
    PrimaryID,
)
from starlette.responses import RedirectResponse
from fluvius.error import ForbiddenError, NotFoundError, BadRequestError
from rfx_user import config as userconf
from . import config

from .state import IDMStateManager
from .domain import IDMDomain
from .policy import IDMPolicyManager
from .types import InvitationStatusEnum
from . import scope


class IDMQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager
    __policymgr__ = IDMPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = IDMDomain.Meta.namespace
        tags = IDMDomain.Meta.tags


resource = IDMQueryManager.register_resource
endpoint = IDMQueryManager.register_endpoint


@endpoint(".accept-invitation/{invitation_id}")
async def accept_invitation(
    query_manager: IDMQueryManager, request: Request, invitation_id: str
):
    async with query_manager.data_manager.transaction():
        token = request.query_params.get("token")
        invitation = await query_manager.data_manager.fetch("invitation", invitation_id)
        if not invitation:
            raise NotFoundError("IDM.404.01", "Invitation not found")

        context = request.state.auth_context
        if not context:
            next_url = f"{request.url.path}?{request.url.query}" if request.url.query else request.url.path
            signin_url = f"/api/auth/sign-in?next={quote(next_url)}"
            return RedirectResponse(signin_url)

        if token != invitation.token:
            raise ForbiddenError("IDM.403.03", "Invalid invitation token")

        if str(invitation.user_id) != str(context.profile.usr_id):
            # Logged in but as the wrong user
            # Use relative URL for redirect_uri to ensure it passes safe redirect validation
            next_url = f"{request.url.path}?{request.url.query}" if request.url.query else request.url.path
            signout_url = f"/api/auth/sign-out?redirect_uri={quote(next_url)}"
            raise ForbiddenError(
                "IDM.403.01",
                f"This invitation (for {invitation.email}) does not belong to your current account ({context.profile.email}).",
                errdata={"sign_out_url": signout_url}
            )

        # Ensure user is verified before accepting invitation
        user = await query_manager.data_manager.fetch("user", context.profile.usr_id)
        if not user:
            raise NotFoundError("IDM.404.02", "User not found")

        if not user.verified_email:
            raise ForbiddenError(
                "IDM.403.02",
                "Please verify your email address before accepting invitations.",
                errdata={"email": user.telecom__email}
            )

        if invitation.status != InvitationStatusEnum.PENDING:
            raise BadRequestError("IDM.400.01", f"Invitation status is {invitation.status}, cannot accept")
        # Only block when there is already a fully ACTIVE profile.
        # An INACTIVE placeholder created by CreateProfileUserInOrg must not block acceptance.
        # Also skip the check when the invitation references its own pre-created profile.
        if not invitation.profile_id:
            existing_profile = await query_manager.data_manager.exist(
                "profile",
                where=dict(
                    user_id=invitation.user_id,
                    organization_id=invitation.organization_id,
                    status="ACTIVE",
                ),
            )
            if existing_profile:
                raise BadRequestError("IDM.400.04", "User already has an active profile in this organization")
        current_time = datetime.now(timezone.utc)
        if invitation.expires_at and invitation.expires_at < current_time:
            await query_manager.data_manager.update(
                invitation, status=InvitationStatusEnum.EXPIRED
            )
            invitation_status_record = dict(
                _id=UUID_GENR(),
                invitation_id=invitation._id,
                src_state=invitation.status,
                dst_state=invitation.status,
            )
            await query_manager.data_manager.add_entry(
                "invitation_status", **invitation_status_record
            )
            raise BadRequestError("IDM.400.02", "Invitation has expired")

        await query_manager.data_manager.update(
            invitation, status=InvitationStatusEnum.ACCEPTED
        )

        invitation_status_record = dict(
            _id=UUID_GENR(),
            invitation_id=invitation._id,
            src_state=InvitationStatusEnum.ACCEPTED,
            dst_state=InvitationStatusEnum.ACCEPTED,
        )
        await query_manager.data_manager.add_entry(
            "invitation_status", **invitation_status_record
        )
        user = await query_manager.data_manager.fetch("user", context.profile.usr_id)
        if not user:
            raise NotFoundError("IDM.404.02", "User not found")

        # Check for existing profile (possibly INACTIVE) to activate
        existing_profile_rec = await query_manager.data_manager.exist(
            "profile",
            where=dict(
                user_id=user._id,
                organization_id=invitation.organization_id,
                realm=invitation.realm
            )
        )

        if existing_profile_rec:
            # Activate existing profile
            src_status = existing_profile_rec.status
            await query_manager.data_manager.update(
                existing_profile_rec,
                status="ACTIVE",
                # Synchronize name/contact info from user record
                name__family=user.name__family,
                name__given=user.name__given,
                telecom__email=user.telecom__email,
            )
            profile_id = existing_profile_rec._id
        else:
            # Create a brand new profile
            src_status = "ACTIVE"
            profile_record = dict(
                _id=UUID_GENR(),
                organization_id=invitation.organization_id,
                user_id=user._id,
                name__family=user.name__family,
                name__given=user.name__given,
                telecom__email=user.telecom__email,
                realm=invitation.realm,
                status="ACTIVE",
            )
            await query_manager.data_manager.add_entry("profile", **profile_record)
            profile_id = profile_record["_id"]

        # Record status transition
        profile_status_record = dict(
            _id=UUID_GENR(),
            profile_id=profile_id,
            src_state=src_status,
            dst_state="ACTIVE",
        )
        await query_manager.data_manager.add_entry(
            "profile_status", **profile_status_record
        )

        # Assign roles from the invitation (default: VIEWER)
        role_keys = invitation.role_keys or ["VIEWER"]
        for role_key in role_keys:
            role = await query_manager.data_manager.exist(
                "ref__system_role", where=dict(key=role_key)
            )
            if not role:
                continue
            await query_manager.data_manager.add_entry(
                "profile_role",
                _id=UUID_GENR(),
                profile_id=profile_id,
                role_key=role_key,
                role_id=role._id,
                role_source="INVITATION",
            )

        redirect_url = userconf.REALM_URL_MAPPER.get(invitation.realm, "/") if userconf.REALM_URL_MAPPER else "/"
        return RedirectResponse(redirect_url, status_code=303)


@endpoint(".reject-invitation/{invitation_id}")
async def reject_invitation(
    query_manager: IDMQueryManager, request: Request, invitation_id: str
):
    async with query_manager.data_manager.transaction():
        token = request.query_params.get("token")
        invitation = await query_manager.data_manager.fetch("invitation", invitation_id)
        if not invitation:
            raise NotFoundError("IDM.404.01", "Invitation not found")

        context = request.state.auth_context
        if not context:
            next_url = f"{request.url.path}?{request.url.query}" if request.url.query else request.url.path
            signin_url = f"/api/auth/sign-in?next={quote(next_url)}"
            return RedirectResponse(signin_url)

        if token != invitation.token:
            raise ForbiddenError("IDM.403.03", "Invalid invitation token")

        if str(invitation.user_id) != str(context.profile.usr_id):
            next_url = f"{request.url.path}?{request.url.query}" if request.url.query else request.url.path
            signout_url = f"/api/auth/sign-out?redirect_uri={quote(next_url)}"
            raise ForbiddenError(
                "IDM.403.01",
                f"This invitation (for {invitation.email}) does not belong to your current account ({context.profile.email}).",
                errdata={"sign_out_url": signout_url}
            )

        # Ensure user is verified before rejecting invitation
        user = await query_manager.data_manager.fetch("user", context.profile.usr_id)
        if not user or not user.verified_email:
            raise ForbiddenError(
                "IDM.403.02",
                "Please verify your email address before rejecting invitations.",
                errdata={"email": user.telecom__email if user else None}
            )

        if invitation.status != "PENDING":
            raise BadRequestError("IDM.400.03", f"Invitation status is {invitation.status}, cannot reject")
        await query_manager.data_manager.update(invitation, status="REJECTED")
        await query_manager.data_manager.add_entry(
            "invitation_status",
            _id=UUID_GENR(),
            invitation_id=invitation._id,
            src_state=invitation.status,
            dst_state=invitation.status,
        )
        return {"success": True}


@endpoint(".check-user-email")
async def check_user_email(
    query_manager: IDMQueryManager, request: Request
):
    """Check whether a user with the given email exists in the local database.

    Query param:
        email (str): the email address to check.

    Returns:
        {"exists": true|false}
    """
    async with query_manager.data_manager.transaction():
        email = request.query_params.get("email").strip().lower()
        if not email:
            return {"error": "email query parameter is required"}

        exists = await query_manager.data_manager.exist(
            "user", where=dict(telecom__email=email)
        )
        return {"exists": bool(exists)}


@resource("user")
class UserQuery(DomainQueryResource):
    """List current user's basic info"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True
        backend_model = "user"

        resource = "user"
        policy_required = True

    id: UUID_TYPE = PrimaryID("User ID")
    name__family: str = StringField("Family Name")
    name__given: str = StringField("Given Name")
    telecom__email: str = StringField("Email")
    telecom__phone: str = StringField("Phone")
    username: str = StringField("Username")
    verified_email: Optional[str] = StringField("Verified Email")
    verified_phone: Optional[str] = StringField("Verified Phone")
    is_super_admin: bool = BooleanField("Is Super Admin")
    status: str = EnumField("Status")


@resource("profile")
class ProfileQuery(DomainQueryResource):
    """List current profile's user"""

    class Meta(DomainQueryResource.Meta):
        allow_item_view = True
        allow_list_view = True

    @classmethod
    def base_query(cls, context, scope):
        return {"organization_id": context.organization._id}

    name__family: str = StringField("Family Name")
    name__given: str = StringField("Given Name")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    telecom__email: str = StringField("Email")
    status: str = StringField("Status")


@resource("user-profile")
class UserProfileQuery(DomainQueryResource):
    """List current profile's users"""

    class Meta(DomainQueryResource.Meta):
        allow_item_view = False
        allow_list_view = True

        backend_model = "_profile_list"
        resource = "profile"
        policy_required = True
        scope_required = scope.ProfileListScopeSchema

    name__family: str = StringField("Family Name")
    name__given: str = StringField("Given Name")
    preferred_name: Optional[str] = StringField("Preferred Name")
    username: str = StringField("Username")
    realm: Optional[str] = StringField("Realm")
    telecom__email: str = StringField("Email")
    telecom__phone: str = StringField("Phone")

    user_id: UUID_TYPE = UUIDField("User ID")
    status: str = StringField("Status")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    organization_name: str = StringField("Organization Name")
    profile_roles: str = StringField("Roles", array=True)


@resource("organization-member")
class ProfileListQuery(DomainQueryResource):
    """List current profile's users"""

    class Meta(DomainQueryResource.Meta):
        allow_item_view = False
        allow_list_view = True

        backend_model = "_org_member"
        resource = "profile"
        policy_required = True
        scope_required = scope.OrgProfileListScopeSchema

    name__family: str = StringField("Family Name")
    name__middle: Optional[str] = StringField("Middle Name")
    name__given: str = StringField("Given Name")
    telecom__email: str = StringField("Email")
    telecom__phone: str = StringField("Phone")
    realm: Optional[str] = StringField("Realm")

    user_id: UUID_TYPE = UUIDField("User ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    organization_name: str = StringField("Organization Name")
    profile_status: str = StringField("Status")
    profile_roles: str = StringField("Roles", array=True)
    policy_count: int = StringField("Policy Count")


@resource("profile-detail")
class ProfileDetailQuery(DomainQueryResource):
    """List current profile's user"""

    class Meta(DomainQueryResource.Meta):
        allow_item_view = True
        allow_list_view = False
        backend_model = "profile"

        resource = "profile"
        policy_required = True

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
    two_factor_authentication: Optional[bool] = BooleanField(
        "Two Factor Authentication"
    )
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


@resource("profile-role")
class ProfileRole(DomainQueryResource):
    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "profile_role"

        resource = "profile"
        policy_required = True
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
        policy_required = True

    user_id: UUID_TYPE = UUIDField("User ID")
    address__city: str = StringField("City")
    address__country: str = StringField("Country")
    address__line1: str = StringField("Address Line 1")
    address__line2: str = StringField("Address Line 2")
    address__postal: str = StringField("Postal Code")
    address__state: str = StringField("State/Province")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


@resource("organization")
class OrganizationDetailQuery(DomainQueryResource):
    """Query organization details"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True
        backend_model = "organization"

        resource = "organization"
        policy_required = True

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


@resource("sent-invitation")
class SentInvitationQuery(DomainQueryResource):
    """List invitations for the current user's profiles"""

    class Meta(DomainQueryResource.Meta):
        allow_item_view = True
        allow_list_view = True

        resource = "invitation"
        backend_model = "invitation"
        policy_required = True
        # scope_required = scope.SentInvitationScopeSchema

    id: UUID_TYPE = PrimaryID("Invitation ID")
    sender_id: UUID_TYPE = UUIDField("Sender User ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    user_id: UUID_TYPE = UUIDField("User ID")
    email: str = StringField("Email")
    status: str = EnumField("Status")
    message: str = StringField("Message")
    expires_at: datetime = StringField("Expiration DateTime")


@resource("received-invitation")
class ReceivedInvitationQuery(DomainQueryResource):
    """List invitations received by the current user's profiles"""

    class Meta(DomainQueryResource.Meta):
        allow_item_view = True
        allow_list_view = True

        backend_model = "invitation"
        resource = "invitation"
        policy_required = True

    id: UUID_TYPE = PrimaryID("Invitation ID")
    sender_id: UUID_TYPE = UUIDField("Sender User ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    user_id: UUID_TYPE = UUIDField("User ID")
    email: str = StringField("Email")
    status: str = EnumField("Status")
    message: str = StringField("Message")
    expires_at: datetime = StringField("Expiration DateTime")


@resource("realm")
class RealmQuery(DomainQueryResource):
    """Query realm information"""
    @classmethod
    def base_query(cls, context, scope):
        if config.OPERATION_VALID_REALMS is None:
            return {}

        return {
            ".or": [
                {"key": realm} for realm in config.OPERATION_VALID_REALMS
            ]
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "realm"

        resource = "realm"

    key: str = StringField("Realm Key")
    display: Optional[str] = StringField("Display Name")
    description: Optional[str] = StringField("Description")
    active: Optional[bool] = BooleanField("Active")


@resource("role")
class RoleQuery(DomainQueryResource):
    """Query role information"""

    class Meta(DomainQueryResource.Meta):
        include_all = False
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref__system_role"

    key: str = StringField("Role Key")
    name: Optional[str] = StringField("Display Name")
    description: Optional[str] = StringField("Description")
    active: Optional[bool] = BooleanField("Active")
    role_type: Optional[str] = StringField("Role Type")
