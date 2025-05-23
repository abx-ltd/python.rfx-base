from fluvius.data import serialize_mapping, DataModel, UUID_GENR
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
        profile = yield agg.create_profile(serialize_mapping(payload))
        yield agg.create_response(serialize_mapping(profile), _type="user-profile-response")

class UpdateProfile(Command):
    class Meta:
        key = "update-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    Data = datadef.UpdateProfilePayload

    async def _process(self, agg, stm, payload):
        yield agg.update_profile(serialize_mapping(payload))

class DeactivateProfile(Command):
    class Meta:
        key = "deactivate-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        yield agg.deactivate_profile()
