"""
RFX User Domain Command Handlers

Comprehensive command pattern implementation for multi-tenant user domain operations.
Provides CQRS-style command handlers that orchestrate business logic through domain
aggregates with Keycloak integration for identity management.

Command Categories:
- User Commands: User lifecycle management, Keycloak synchronization, action tracking
- Organization Commands: Multi-tenant organization CRUD and custom role management
- Invitation Commands: Secure organization invitation workflow with token validation
- Profile Commands: User profile management within organizational contexts
- Group Commands: Security group operations and profile associations

All commands enforce authentication, authorization policies, and maintain audit trails
through the Fluvius domain aggregate pattern with event sourcing capabilities.

Integration Points:
- Keycloak Admin API for identity operations
- Domain aggregates for business logic orchestration
- State manager for persistence and event tracking
- Policy engine for authorization decisions
"""

from datetime import datetime
from fluvius.data import serialize_mapping, UUID_GENR

from .domain import UserProfileDomain
from .integration import kc_admin
from . import datadef

processor = UserProfileDomain.command_processor
Command = UserProfileDomain.Command


# ==========================================================================
# USER COMMANDS
# User lifecycle management with Keycloak integration for identity operations
# ==========================================================================

# Need usecase for create-user command.
# class CreateUser(Command):
#     class Meta:
#         key = "create-user"
#         resources = ("user",)
#         tags = ["user"]
#         resource_init = True
#         auth_required = True

# class UpdateUser(Command):
#     class Meta:
#         key = "update-user"
#         resources = ("user",)
#         tags = ["user"]
#         auth_required = True

# class SendAction(Command):
#     """
#     Send required actions to user in Keycloak (e.g., UPDATE_PASSWORD, VERIFY_EMAIL).
#     Manages user action requirements and integrates with Keycloak's action execution system.
#     Updates user's required actions list if marked as required for enforcement.
#     """
#     class Meta:
#         key = "send-action"
#         resources = ("user",)
#         tags = ["user"]
#         auth_required = True
#         policy_required = False

#     Data = datadef.SendActionPayload

#     async def _process(self, agg, stm, payload):
#         rootobj = agg.get_rootobj()
#         user_id = rootobj._id

#         await kc_admin.execute_actions(user_id=user_id, actions=payload.actions, redirect_uri=config.REDIRECT_URL)
#         await agg.track_user_action(payload)

#         if payload.required:
#             kc_user = await kc_admin.get_user(user_id)
#             required_action = kc_user.requiredActions
#             actions = [
#                 action for action in payload.actions if action not in required_action]
#             required_action.extend(actions)
#             await kc_admin.update_user(user_id=user_id, payload={"requiredActions": required_action})


# class SendVerification(Command):
#     """
#     Send email verification request to user through Keycloak.
#     Updates user record with verification request timestamp for tracking.
#     """
#     class Meta:
#         key = "send-verification"
#         resources = ("user",)
#         tags = ["user"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         rootobj = agg.get_rootobj()
#         await kc_admin.send_verify_email(rootobj._id)
#         await agg.update_user(dict(last_verified_request=datetime.utcnow()))


# class DeactivateUser(Command):
#     """
#     Deactivate user account in both local system and Keycloak.
#     Disables user login while preserving account data for potential reactivation.
#     """
#     class Meta:
#         key = "deactivate-user"
#         resources = ("user",)
#         tags = ["user"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         rootobj = agg.get_rootobj()
#         await kc_admin.update_user(rootobj._id, dict(enabled=False))
#         await agg.deactivate_user()


# class ActivateUser(Command):
#     """
#     Reactivate previously deactivated user account.
#     Enables user login in both Keycloak and local system state.
#     """
#     class Meta:
#         key = "activate-user"
#         resources = ("user",)
#         tags = ["user"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         rootobj = agg.get_rootobj()
#         await kc_admin.update_user(rootobj._id, dict(enabled=True))
#         await agg.activate_user()


# class SyncUser(Command):
#     """
#     Synchronize user information from Keycloak to local system.
#     Implements intelligent sync with rate limiting (5-minute minimum interval)
#     unless force flag is used. Retrieves user profile, roles, and verification status.
#     """

#     class Meta:
#         key = "sync-user"
#         resources = ("user",)
#         tags = ["user"]
#         auth_required = True
#         description = "Synchronize user information from Keycloak"

#     Data = datadef.SyncUserPayload

#     async def _process(self, agg, stm, payload):
#         # Check if sync is needed
#         if not payload.force:
#             user = agg.get_rootobj()
#             if user.last_sync:
#                 # Don't sync if last sync was less than 5 minutes ago
#                 if (datetime.utcnow() - user.last_sync).total_seconds() < 300:
#                     yield agg.create_response(
#                         {"status": "skipped", "reason": "Recently synced"},
#                         _type="user-profile-response",
#                     )
#                     return

#         # Get user info from Keycloak
#         user_id = agg.get_rootobj()._id
#         kc_user = await kc_admin.get_user(user_id)
#         if not kc_user:
#             raise ValueError(f"User {user_id} not found in Keycloak")

#         # Extract user data from Keycloak response
#         user_data = {
#             "name__family": kc_user.lastName,
#             "name__given": kc_user.firstName,
#             "telecom__email": kc_user.email,
#             "username": kc_user.username,
#             "active": kc_user.enabled,
#             "realm_access": kc_user.realmRoles,
#             "resource_access": kc_user.clientRoles,
#             "verified_email": kc_user.emailVerified and kc_user.email,
#             "last_sync": datetime.utcnow(),
#         }

#         # Get required actions
#         required_actions = []
#         if hasattr(kc_user, "requiredActions"):
#             required_actions = kc_user.requiredActions

#         # Create sync payload with Keycloak data
#         sync_payload = datadef.SyncUserPayload(
#             force=payload.force,
#             sync_actions=payload.sync_actions,
#             user_data=user_data,
#             required_actions=required_actions,
#         )

#         # Perform sync
#         user = await agg.sync_user(sync_payload)
#         yield agg.create_response(
#             serialize_mapping(user), _type="user-profile-response"
#         )


# ==========================================================================
# ORGANIZATION COMMANDS
# Multi-tenant organization management with automatic profile creation
# ==========================================================================


# class CreateOrganization(Command):
#     """
#     Create new organization with creator as initial admin profile.
#     Automatically generates profile for organization creator with full permissions
#     and sets up organizational context for multi-tenant operations.
#     """

#     Data = datadef.CreateOrganizationPayload

#     class Meta:
#         key = "create-organization"
#         resource_init = True
#         resources = ("organization",)
#         tags = ["organization", "create"]
#         auth_required = True
#         policy_required = True

#     async def _process(self, agg, stm, payload):
#         profile_id = UUID_GENR()
#         org_data = serialize_mapping(payload)
#         org_data.update(profile_id=profile_id, creator=profile_id)
#         org = await agg.create_organization(payload)

#         context = agg.get_context()
#         user = await stm.fetch("user", context.user_id)
#         profile_data = dict(
#             _id=profile_id,
#             user_id=user._id,
#             organization_id=org._id,
#             name__family=user.name__family,
#             name__given=user.name__given,
#             name__middle=user.name__middle,
#             name__prefix=user.name__prefix,
#             name__suffix=user.name__suffix,
#             telecom__email=user.telecom__email,
#             telecom__phone=user.telecom__phone,
#             status="ACTIVE",
#             current_profile=False,
#         )
#         await agg.create_profile(profile_data)

#         profile_role = dict(
#             profile_id=profile_id, role_key="OWNER", role_source="SYSTEM"
#         )
#         await agg.assign_role_to_profile(data=profile_role)
#         yield agg.create_response(serialize_mapping(org), _type="user-profile-response")


class UpdateOrganization(Command):
    """
    Update organization information and settings.
    Modifies organizational metadata while preserving structural relationships.
    """

    Data = datadef.UpdateOrganizationPayload

    class Meta:
        key = "update-organization"
        resources = ("organization",)
        tags = ["organization", "update"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        await agg.update_organization(payload)
        yield agg.create_response({"status": "success"}, _type="user-profile-response")


# class DeactivateOrganization(Command):
#     """
#     Deactivate organization and all associated profiles.
#     Soft deletion that preserves data while preventing active operations.
#     """

#     class Meta:
#         key = "deactivate-organization"
#         resources = ("organization",)
#         tags = ["organization", "deactivate"]
#         auth_required = True

#     async def _process(self, agg, stm, payload):
#         await agg.deactivate_organization()


# ---------- Organization Role Context -------
# class CreateOrgRole(Command):
#     """
#     Create custom organization-specific role with defined permissions.
#     Enables fine-grained access control within organizational boundaries.
#     """

#     class Meta:
#         key = "create-org-role"
#         resources = ("organization",)
#         tags = ["organization"]
#         auth_required = True
#         resource_init = True
#         policy_required = True

#     Data = datadef.CreateOrgRolePayload

#     async def _process(self, agg, stm, payload):
#         result = await agg.create_org_role(serialize_mapping(payload))
#         yield agg.create_response(result, _type="user-profile-response")


# class UpdateOrgRole(Command):
#     """
#     Update organization role permissions and metadata.
#     Modifies role definition while maintaining existing assignments.
#     """

#     class Meta:
#         key = "update-org-role"
#         resources = ("organization",)
#         tags = ["organization"]
#         auth_required = True
#         policy_required = True

#     Data = datadef.UpdateOrgRolePayload

#     async def _process(self, agg, stm, payload):
#         result = await agg.update_org_role(serialize_mapping(payload))
#         return agg.create_response(result, _type="user-profile-response")


class RemoveOrgRole(Command):
    """
    Remove organization role and revoke from all profiles.
    Cascades removal to prevent orphaned role assignments.
    """

    class Meta:
        key = "remove-org-role"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True

    Data = datadef.RemoveOrgRolePayload

    async def _process(self, agg, stm, payload):
        await agg.remove_org_role(payload)


# class CreateOrgType(Command):
#     """
#     Create new organization type for categorization and management.
#     Establishes organizational classifications for reporting and access control.
#     """
#     class Meta:
#         key = "create-org-type"
#         resource_init = True
#         resources = ("organization",)
#         tags = ["organization-type"]
#         auth_required = True
#         policy_required = True

#     Data = datadef.CreateOrgTypePayload

#     async def _process(self, agg, stm, payload):
#         result = await agg.create_org_type(serialize_mapping(payload))
#         yield agg.create_response(serialize_mapping(result), _type="user-profile-response")

# class RemoveOrgType(Command):
#     """
#     Remove organization type and revoke from all profiles.
#     Cascades removal to prevent orphaned role assignments.
#     """
#     class Meta:
#         key = "remove-org-type"
#         resources = ("organization",)
#         tags = ["organization-type"]
#         auth_required = True
#         policy_required = True

#     Data = datadef.RemoveOrgTypePayload

#     async def _process(self, agg, stm, payload):
#         result = await agg.remove_org_type(serialize_mapping(payload))
#         yield agg.create_response(result, _type="user-profile-response")


# ---------- Invitation Context -------
class SendInvitation(Command):
    """
    Send secure invitation to join organization.
    Generates unique token with expiration and handles existing user detection.
    """

    class Meta:
        key = "send-invitation"
        resources = ("invitation",)
        tags = ["invitation"]
        auth_required = True
        resource_init = True
        policy_required = True

    Data = datadef.SendInvitationPayload

    async def _process(self, agg, stm, payload):
        result = await agg.send_invitation(serialize_mapping(payload))
        yield agg.create_response(result, _type="user-profile-response")


class ResendInvitation(Command):
    """
    Resend invitation with new token and extended expiry.
    Refreshes invitation security while maintaining original invitation context.
    """

    class Meta:
        key = "resend-invitation"
        resources = ("invitation",)
        tags = ["invitation"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.resend_invitation()
        yield agg.create_response(result, _type="user-profile-response")


class RevokeInvitation(Command):
    """
    Cancel pending invitation to prevent acceptance.
    Invalidates invitation token while preserving audit trail.
    """

    class Meta:
        key = "revoke-invitation"
        resources = ("invitation",)
        tags = ["invitation"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.revoke_invitation()
        yield agg.create_response(result, _type="user-profile-response")


# ---------- Profile Context ----------


class CreateProfile(Command):
    """
    Create user profile within organizational context.
    Establishes user presence and permissions within specific organization.
    """

    class Meta:
        key = "create-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        resource_init = True
        policy_required = True

    Data = datadef.CreateProfilePayload

    async def _process(self, agg, stm, payload):
        data = serialize_mapping(payload)
        profile_role_key = data.pop("profile_role_key", "VIEWER")
        profile_role_source = data.pop("profile_role_source", "SYSTEM")
        profile = await agg.create_profile(data)
        profile_role = dict(
            profile_id=profile._id,
            role_key=profile_role_key,
            role_source=profile_role_source,
        )
        await agg.assign_role_to_profile(profile_role)
        yield agg.create_response(
            serialize_mapping(profile), _type="user-profile-response"
        )


class SwitchProfile(Command):
    """
    Switch active organization for user profile.
    Updates current profile's organization context for multi-tenant operations.
    """

    class Meta:
        key = "switch-profile"
        resources = ("profile",)
        tags = ["profile", "switch"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        await agg.switch_profile()


class UpdateProfile(Command):
    """
    Update profile information and organizational settings.
    Modifies profile metadata while maintaining organizational relationships.
    """

    class Meta:
        key = "update-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        policy_required = True

    Data = datadef.UpdateProfilePayload

    async def _process(self, agg, stm, payload):
        await agg.update_profile(payload)
# ---------- Profile Role ----------


class AssignRoleToProfile(Command):
    """
    Assign system or organization role to profile.
    Grants specific permissions within organizational context.
    """

    class Meta:
        key = "assign-role-to-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        policy_required = True

    Data = datadef.AssignRolePayload

    async def _process(self, agg, stm, payload):
        role = await agg.assign_role_to_profile(serialize_mapping(payload))
        agg.create_response(role, _type="user-profile-response")


class RevokeRoleFromProfile(Command):
    """
    Revoke specific role from profile.
    Removes individual role assignment while maintaining other permissions.
    """

    class Meta:
        key = "revoke-role-from-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    Data = datadef.RevokeRolePayload

    async def _process(self, agg, stm, payload):
        await agg.revoke_role_from_profile(serialize_mapping(payload))


class ClearAllRoleFromProfile(Command):
    """
    Remove all roles assigned to profile.
    Clears all role assignments while maintaining profile structure.
    """

    class Meta:
        key = "clear-role-from-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        internal = True

    async def _process(self, agg, stm, payload):
        await agg.clear_all_role_from_profile()


class DeactivateProfile(Command):
    """
    Deactivate profile within organization.
    Removes profile access while preserving organizational history.
    """

    class Meta:
        key = "deactivate-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        await agg.deactivate_profile()

class ActivateProfile(Command):
    """
    Reactivate previously deactivated profile.
    Restores profile access within organizational context.
    """

    class Meta:
        key = "activate-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        await agg.activate_profile()


class DeleteProfile(Command):
    """
    Delete user profile within organization.
    Removes profile and associated data from system.
    """

    class Meta:
        key = "delete-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        await agg.delete_profile()


# class AddGroupToProfile(Command):
#     """
#     Add profile to security group.
#     Associates profile with group for permissions and organization structure.
#     """

#     class Meta:
#         key = "add-group-to-profile"
#         resources = ("profile",)
#         tags = ["profile"]
#         auth_required = True
#         internal = True

#     Data = datadef.AddGroupToProfilePayload

#     async def _process(self, agg, stm, payload):
#         await agg.add_group_to_profile(payload)


# class RemoveGroupFromProfile(Command):
#     """
#     Remove profile from security group.
#     Removes group association while preserving other group memberships.
#     """

#     class Meta:
#         key = "remove-group-from-profile"
#         resources = ("profile",)
#         tags = ["profile"]
#         auth_required = True
#         internal = True

#     Data = datadef.RemoveGroupFromProfilePayload

#     async def _process(self, agg, stm, payload):
#         await agg.remove_group_from_profile(payload)


# ============ Group Context =============


# class AssignGroupToProfile(Command):
#     """
#     Assign security group to profile with permissions validation.
#     Creates group membership within organizational security model.
#     """

#     class Meta:
#         key = "assign-group-to-profile"
#         resources = ("profile",)
#         tags = ["profile"]
#         auth_required = True
#         internal = True

#     Data = datadef.AddGroupToProfilePayload

#     async def _process(self, agg, stm, payload):
#         group = await agg.assign_group_to_profile(payload)
#         yield agg.create_response(
#             serialize_mapping(group), _type="user-profile-response"
#         )


# class RevokeGroupFromProfile(Command):
#     """
#     Revoke group membership from profile.
#     Removes specific group association while maintaining other memberships.
#     """

#     class Meta:
#         key = "revoke-group-from-profile"
#         resources = ("profile",)
#         tags = ["profile"]
#         auth_required = True
#         internal = True

#     Data = datadef.RemoveGroupFromProfilePayload

#     async def _process(self, agg, stm, payload):
#         await agg.revoke_group_from_profile(payload)
#         yield agg.create_response({"status": "success"}, _type="user-profile-response")


# class ClearAllGroupFromProfile(Command):
#     """
#     Remove all group memberships from profile.
#     Clears all group associations while preserving profile structure.
#     """

#     class Meta:
#         key = "clear-group-from-profile"
#         resources = ("profile",)
#         tags = ["profile"]
#         auth_required = True
#         internal = True

#     async def _process(self, agg, stm, payload):
#         await agg.clear_all_group_from_profile()
#         yield agg.create_response({"status": "success"}, _type="user-profile-response")


# class CreateGroup(Command):
#     """
#     Create new security group with organizational scope.
#     Establishes group structure for permissions and access management.
#     """

#     class Meta:
#         key = "create-group"
#         resource_init = True
#         resources = ("group",)
#         tags = ["group"]
#         auth_required = True
#         description = "Create a new group"
#         internal = True

#     Data = datadef.CreateGroupPayload

#     async def _process(self, agg, stm, payload):
#         group = await agg.create_group(payload)
#         yield agg.create_response(
#             serialize_mapping(group), _type="user-profile-response"
#         )


# class UpdateGroup(Command):
#     """
#     Update security group metadata and permissions.
#     Modifies group definition while maintaining existing memberships.
#     """

#     class Meta:
#         key = "update-group"
#         resources = ("group",)
#         tags = ["group"]
#         auth_required = True
#         description = "Update an existing group"
#         internal = True

#     Data = datadef.UpdateGroupPayload

#     async def _process(self, agg, stm, payload):
#         group = await agg.update_group(payload)
#         yield agg.create_response(
#             serialize_mapping(group), _type="user-profile-response"
#         )


# class DeleteGroup(Command):
#     """
#     Soft delete security group and remove all profile associations.
#     Deactivates group while preserving audit trail and historical memberships.
#     """

#     class Meta:
#         key = "delete-group"
#         resources = ("group",)
#         tags = ["group"]
#         auth_required = True
#         description = "Delete (soft) a group and remove all profile associations"
#         internal = True

#     async def _process(self, agg, stm, payload):
#         await agg.delete_group()
#         yield agg.create_response({"status": "success"}, _type="user-profile-response")

#     async def _process(self, agg, stm, payload):
#         await agg.delete_group()
#         yield agg.create_response({"status": "success"}, _type="user-profile-response")
