import secrets
from datetime import datetime, timedelta
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping
from .types import OrganizationStatus, ProfileStatus, UserStatus, InvitationStatus


class UserProfileAggregate(Aggregate):
    async def set_org_status(self, org, status, note=None):
        record = self.init_resource("organization-status",
            organization_id=org._id,
            src_state=org.status,
            dst_state=status,
            note=note
        )
        await self.statemgr.insert(record)

    async def set_profile_status(self, profile, status, note=None):
        record = self.init_resource("profile-status",
            profile_id=profile._id,
            src_state=profile.status,
            dst_state=status,
            note=note
        )
        await self.statemgr.insert(record)

    async def set_user_status(self, user, status, note=None):
        record = self.init_resource("user-status",
            user_id=user._id,
            src_state=user.status,
            dst_state=status,
            note=note
        )
        await self.statemgr.insert(record)
    # =========== User Context ============
    @action("user-action-tracked", resources="user")
    async def track_user_action(self, stm, /, data):
        for _action in data.actions:
            record = self.init_resource('user-action', dict(
                user_id=self.context.user_id,
                action=_action,
                name=_action
            ))
            await self.statemgr.insert(record)

    @action("user-updated", resources="user")
    async def update_user(self, stm, /, data):
        item = self.rootobj
        await stm.update(item, **serialize_mapping(data))
        if getattr(data, "status", None) and item.status != data.status:
            await self.set_user_status(item, data.status)
        return item

    @action("user-deactivated", resources="user")
    async def deactivate_user(self, stm, /, data):
        item = self.rootobj
        await stm.update(item, status=UserStatus.DEACTIVATED)
        await self.set_user_status(item, UserStatus.DEACTIVATED)

    @action("user-activated", resources="user")
    async def activate_user(self, stm, /, data):
        item = self.rootobj
        await stm.update(item, status=UserStatus.ACTIVE)
        await self.set_user_status(item, UserStatus.ACTIVE)

    # =========== Organization Context ============
    @action("organization-created", resources="organization", emit_event=True)
    async def create_organization(self, stm, /, data):
        record = self.init_resource(
            "organization",
            serialize_mapping(data),
            _id=self.aggroot.identifier,
            status=getattr(data, "status", "SETUP")
        )
        await stm.insert(record)
        await self.set_org_status(record, record.status)
        return record

    @action("organization-updated", resources="organization", emit_event=True)
    async def update_organization(self, stm, /, data):
        item = self.rootobj
        await stm.update(item, **serialize_mapping(data))
        if getattr(data, "status", None) and item.status != data.status:
            await self.set_org_status(item, data.status)

        return item

    @action("organization-deactivated", resources="organization")
    async def deactivate_organization(self, stm, /, data=None):
        item = self.rootobj
        await stm.update(item, status=OrganizationStatus.INACTIVE)
        await self.set_org_status(item, OrganizationStatus.INACTIVE)

    # =========== Invitation Context ============
    async def set_invitation_status(self, invitation, new_status: InvitationStatus, note=None):
        status_record = self.init_resource("invitation-status",
            invitation_id=invitation._id,
            src_state=invitation.status,
            dst_state=new_status.value,
            note=note
        )
        await self.statemgr.insert(status_record)

    @action("invitation-sent", resources="invitation")
    async def send_invitation(self, stm, /, data):
        token = secrets.token_urlsafe(16)
        record = self.init_resource("invitation", {
            **serialize_mapping(data),
            "token": token,
            "status": InvitationStatus.PENDING.value,
            "expires_at": datetime.utcnow() + timedelta(days=7)
        })
        await stm.insert(record)
        await self.set_invitation_status(record, InvitationStatus.PENDING, "Initial invitation sent")
        return {"_id": record._id}

    @action("invitation-resent", resources="invitation")
    async def resend_invitation(self, stm, /):
        invitation = self.rootobj
        updates = {
            "token": secrets.token_urlsafe(16),
            "status": InvitationStatus.PENDING.value,
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        await stm.update(invitation, **updates)
        await self.set_invitation_status(invitation, InvitationStatus.PENDING, "Invitation resent")
        return {"_id": invitation._id, "resend": True}

    @action("invitation-revoked", resources="invitation")
    async def revoke_invitation(self, stm, /):
        invitation = self.rootobj
        await stm.update(invitation, status=InvitationStatus.REVOKED)
        await self.set_invitation_status(invitation, InvitationStatus.REVOKED, "Invitation revoked")
        return {"_id": invitation._id, "revoked": True}

    @action("invitation-accepted", resources="invitation")
    async def accept_invitation(self, stm, /):
        invitation = self.rootobj

        if invitation.status != InvitationStatus.PENDING.value:
            raise ValueError("Only PENDING invitations can be accepted.")

        await stm.update(invitation, status=InvitationStatus.ACCEPTED)
        await self.set_invitation_status(invitation, InvitationStatus.ACCEPTED, "Invitation accepted")
        return {"_id": invitation._id, "accepted": True}

    @action("invitation-rejected", resources="invitation")
    async def reject_invitation(self, stm, /):
        invitation = self.rootobj

        if invitation.status != InvitationStatus.PENDING.value:
            raise ValueError("Only PENDING invitations can be rejected.")

        await stm.update(invitation, status=InvitationStatus.REJECTED)
        await self.set_invitation_status(invitation, InvitationStatus.REJECTED, "Invitation rejected")
        return {"_id": invitation._id, "rejected": True}

    # =========== Profile Context ============
    @action("profile-created", resources=("organization", "profile"))
    async def create_profile(self, stm, /, data):
        record = self.init_resource(
            "profile",
            serialize_mapping(data),
            status=getattr(data, "status", "ACTIVE")
        )
        await stm.insert(record)
        await self.set_profile_status(record, record.status)
        return record

    @action("profile-updated", resources="profile", emit_event=True)
    async def update_profile(self, stm, /, data):
        item = self.rootobj
        await stm.update(item, **serialize_mapping(data))
        if getattr(data, "status", None) and item.status != data.status:
            await self.set_profile_status(item, data.status)

        return item

    @action("profile-deactivated", resources="profile")
    async def deactivate_profile(self, stm, /, data=None):
        item = self.rootobj
        await stm.update(item, status=ProfileStatus.DEACTIVATED)
        await self.set_profile_status(item, ProfileStatus.DEACTIVATED)

    # =========== Group Context ==========
    @action("group-created", resources="group")
    async def create_group(self, stm, /, data):
        record = self.init_resource("group", data)
        await stm.insert(record)
        return {"_id": record._id}

    @action("group-updated", resources="group")
    async def update_group(self, stm, /, data):
        await stm.update(self.rootobj, **serialize_mapping(data))
        return {"updated": True}

    @action("group-deleted", resources="group")
    async def delete_group(self, stm, /):
        await stm.invalidate_one("group", identifier=self.rootobj._id)
        return {"deleted": True}
