from datetime import datetime
from fluvius.data import serialize_mapping, DataModel, UUID_GENR

from .domain import UserProfileDomain
from .integration import kc_admin
from . import datadef, config

processor = UserProfileDomain.command_processor
Command = UserProfileDomain.Command


# ---------- User Context ----------
# Need usecase for create-user command.
# class CreateUser(Command):
#     class Meta:
#         key = "create-user"
#         resources = ("user",)
#         tags = ["user"]
#         new_resource = True
#         auth_required = True

# class UpdateUser(Command):
#     class Meta:
#         key = "update-user"
#         resources = ("user",)
#         tags = ["user"]
#         auth_required = True

class SendAction(Command):
    class Meta:
        key = "send-action"
        resources = ("user",)
        tags = ["user"]
        auth_required = True

    Data = datadef.SendActionPayload

    async def _process(self, agg, stm, payload):
        rootobj = agg.get_rootobj()
        user_id = rootobj._id

        await kc_admin.execute_actions(user_id=user_id, actions=payload.actions, redirect_uri=config.REDIRECT_URL)
        await agg.track_user_action(payload)

        if payload.required:
            kc_user = await kc_admin.get_user(user_id)
            required_action = kc_user.requiredActions
            actions = [action for action in payload.actions if action not in required_action]
            required_action.extend(actions)
            await kc_admin.update_user(user_id=user_id, payload={"requiredActions": required_action})


class SendVerification(Command):
    class Meta:
        key = "send-verification"
        resources = ("user",)
        tags = ["user"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        rootobj = agg.get_rootobj()
        await kc_admin.send_verify_email(rootobj._id)
        await agg.update_user(dict(last_verified_request=datetime.utcnow()))


class DeactivateUser(Command):
    class Meta:
        key = "deactivate-user"
        resources = ("user",)
        tags = ["user"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        rootobj = agg.get_rootobj()
        await kc_admin.update_user(rootobj._id, dict(enabled=False))
        await agg.deactivate_user()


class ActivateUser(Command):
    class Meta:
        key = "activate-user"
        resources = ("user",)
        tags = ["user"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        rootobj = agg.get_rootobj()
        await kc_admin.update_user(rootobj._id, dict(enabled=True))
        await agg.activate_user()


# ---------- Organization Context ----------
class CreateOrganization(Command):
    Data = datadef.CreateOrganizationPayload

    class Meta:
        key = "create-organization"
        new_resource = True
        resources = ("organization",)
        tags = ["organization", "create"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        profile_id = UUID_GENR()
        org_data = serialize_mapping(payload)
        org_data.update(profile_id=profile_id, creator=profile_id)
        org = await agg.create_organization(payload)

        context = agg.get_context()
        user = await stm.fetch("user", context.user_id)
        profile_data = dict(
            _id=profile_id,
            user_id=user._id,
            organization_id=org._id,
            name__family=user.name__family,
            name__given=user.name__given,
            name__middle=user.name__middle,
            name__prefix=user.name__prefix,
            name__suffix=user.name__suffix,
            telecom__email=user.telecom__email,
            telecom__phone=user.telecom__phone,
            status='ACTIVE',
            current_profile=True
        )
        await agg.create_profile(profile_data)
        yield agg.create_response(serialize_mapping(org), _type="user-profile-response")


class UpdateOrganization(Command):
    Data = datadef.UpdateOrganizationPayload

    class Meta:
        key = "update-organization"
        resources = ("organization",)
        tags = ["organization", "update"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.update_organization(payload)
        yield agg.create_response({"status": "success"}, _type="user-profile-response")


class DeactivateOrganization(Command):
    class Meta:
        key = "deactivate-organization"
        resources = ("organization",)
        tags = ["organization", "deactivate"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.deactivate_organization()


# ---------- Organization Role Context -------
class CreateOrgRole(Command):
    class Meta:
        key = "create-org-role"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True
        new_resource = True

    Data = datadef.CreateOrgRolePayload

    async def _process(self, agg, stm, payload):
        role = await agg.create_org_role(payload)
        yield agg.create_response(serialize_mapping(role), _type="user-profile-response")


class UpdateOrgRole(Command):
    class Meta:
        key = "update-org-role"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True
        new_resource = True

    Data = datadef.UpdateOrgRolePayload

    async def _process(self, agg, stm, payload):
        await agg.update_org_role(payload)


class DeleteOrgRole(Command):
    class Meta:
        key = "delete-org-role"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True
        new_resource = True

    Data = datadef.DeleteOrgRolePayload

    async def _process(self, agg, stm, payload):
        await agg.remove_org_role(payload)


# ---------- Invitation Context -------
class SendInvitation(Command):
    class Meta:
        key = "send-invitation"
        resources = ("invitation",)
        tags = ["invitation"]
        auth_required = True
        new_resource = True

    Data = datadef.SendInvitationPayload

    async def _process(self, agg, stm, payload):
        invitation = await agg.send_invitation(payload)
        yield agg.create_response(serialize_mapping(invitation), _type="user-profile-response")

class ResendInvitation(Command):
    class Meta:
        key = "resend-invitation"
        resources = ("invitation",)
        tags = ["invitation"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.resend_invitation(payload)

class RevokeInvitation(Command):
    class Meta:
        key = "revoke-invitation"
        resources = ("invitation",)
        tags = ["invitation"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.revoke_invitation(payload)

class AcceptInvitation(Command):
    class Meta:
        key = "accept-invitation"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.accept_invitation(payload)

class RejectInvitation(Command):
    class Meta:
        key = "reject-invitation"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.reject_invitation(payload)

# ---------- Profile Context ----------
class CreateProfile(Command):
    class Meta:
        key = "create-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        new_resource = True

    Data = datadef.CreateProfilePayload

    async def _process(self, agg, stm, payload):
        profile = yield agg.create_profile(payload)
        yield agg.create_response(serialize_mapping(profile), _type="user-profile-response")

class UpdateProfile(Command):
    class Meta:
        key = "update-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    Data = datadef.UpdateProfilePayload

    async def _process(self, agg, stm, payload):
        yield agg.update_profile(payload)

class DeactivateProfile(Command):
    class Meta:
        key = "deactivate-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        yield agg.deactivate_profile()

# ---------- Profile Role ----------
class AssignRoleToProfile(Command):
    class Meta:
        key = "assign-role-to-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    Data = datadef.AssignRolePayload

    async def _process(self, agg, stm, payload):
        role = await agg.assign_role_to_profile(payload)
        yield agg.create_response(serialize_mapping(role), _type="user-profile-response")

class RevokeRoleFromProfile(Command):
    class Meta:
        key = "revoke-role-from-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    Data = datadef.RevokeRolePayload

    async def _process(self, agg, stm, payload):
        await agg.revoke_role_from_profile(payload)

class ClearAllRoleFromProfile(Command):
    class Meta:
        key = "clear-role-from-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.clear_all_role_from_profile()

class AddGroupToProfile(Command):
    class Meta:
        key = "add-group-to-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    Data = datadef.AddGroupToProfilePayload

    async def _process(self, agg, stm, payload):
        await agg.add_group_to_profile(payload)

class RemoveGroupFromProfile(Command):
    class Meta:
        key = "remove-group-from-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    Data = datadef.RemoveGroupFromProfilePayload

    async def _process(self, agg, stm, payload):
        await agg.remove_group_from_profile(payload)

# ============ Group Context =============
class CreateGroupCmd(Command):
    class Meta:
        key = "create-group"
        new_resource = True
        resources = ("group",)
        description = "Create a new group"

    Data = datadef.CreateGroupPayload

    @processor
    async def _process(self, agg, stm, payload):
        group = await agg.create_group(payload)
        yield agg.create_response(serialize_mapping(group), _type="user-profile-response")

class UpdateGroupCmd(Command):
    class Meta:
        key = "update-group"
        new_resource = False
        resources = ("group",)
        description = "Update an existing group"

    Data = datadef.UpdateGroupPayload

    @processor
    async def _process(self, agg, stm, payload):
        await agg.update_group(payload)

class DeleteGroupCmd(Command):
    class Meta:
        key = "delete-group"
        new_resource = False
        resources = ("group", )
        description = "Delete (soft) a group"

    @processor
    async def _process(self, agg, stm, payload):
        await agg.delete_group()
