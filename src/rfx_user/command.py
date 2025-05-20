from fluvius.data import serialize_mapping, DataModel
from .domain import UserProfileDomain
from . import datadef

processor = UserProfileDomain.command_processor
Command = UserProfileDomain.Command


# ---------- User Context ----------
class DeactivateUser(Command):
    pass

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
        org = await agg.create_organization(payload)
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


# ---------- Profile Context ----------
class UpdateProfile(Command):
    class Meta:
        key = "update-profile"
        resources = ("user-profile",)
        tags = ["profile", "update"]
        auth_required = True


class DeactivateProfile(Command):
    class Meta:
        key = "deactivate-profile"
        resources = ("user-profile",)
        tags = ["profile", "deactivate"]
        auth_required = True
