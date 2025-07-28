import secrets
from datetime import datetime, timedelta
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, UUID_GENR
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

    @action("user-synced", resources="user")
    async def sync_user(self, stm, /, data):
        user = self.rootobj
        await stm.update(user, **data.user_data)

        # Handle user actions
        if data.sync_actions:
            # Get current pending actions from database
            current_actions = await stm.find_all('user-action', where=dict(
                user_id=user._id,
                status='PENDING'
            ))

            # If there are required actions from Keycloak, update or create them
            if data.required_actions:
                # Track which actions we've seen
                processed_actions = set()

                for action in data.required_actions:
                    # Try to find existing action
                    existing = next(
                        (a for a in current_actions if a.action == action), None)

                    if existing:
                        # Action already exists, mark as seen
                        processed_actions.add(existing._id)
                    else:
                        # Create new action record
                        record = self.init_resource('user-action', dict(
                            user_id=user._id,
                            action=action,
                            name=action,
                            status='PENDING'
                        ))
                        await self.statemgr.insert(record)

                # Any current actions not in required_actions should be marked as completed
                for action in current_actions:
                    if action._id not in processed_actions:
                        await stm.update(action, status='COMPLETED')
            else:
                # If no required actions, mark all pending actions as completed
                for action in current_actions:
                    await stm.update(action, status='COMPLETED')

        return user

    # =========== Organization Context ============
    @action("organization-created", resources="organization")
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

    @action("organization-updated", resources="organization")
    async def update_organization(self, stm, /, data):
        item = self.rootobj
        await stm.update(item, **serialize_mapping(data))
        if getattr(data, "status", None) and item.status != data.status:
            await self.set_org_status(item, data.status)

        return item

    @action("organization-deactivated", resources="organization")
    async def deactivate_organization(self, stm, /, data=None):
        item = self.rootobj
        await stm.update(item, status=OrganizationStatus.DEACTIVATED)
        await self.set_org_status(item, OrganizationStatus.DEACTIVATED)

    @action("org-role-created", resources="organization")
    async def create_org_role(self, stm, /, data):
        record = self.init_resource(
            "organization-role",
            serialize_mapping(data),
            _id=UUID_GENR(),
            organization_id=self.aggroot.identifier
        )
        await stm.insert(record)
        return {"role_id": record._id}

    @action("org-role-updated", resources="organization")
    async def update_org_role(self, stm, /, data):
        item = await stm.fetch('organization-role', data.role_id, organization_id=self.aggroot.identifier)
        await stm.update(item, **serialize_mapping(data.updates))
        return {"updated": True}

    @action("org-role-removed", resources="organization")
    async def remove_org_role(self, stm, /, data):
        item = await stm.fetch('organization-role', data.role_id, organization_id=self.aggroot.identifier)
        await stm.invalidate_one("organization-role", item._id)
        return {"removed": True}

    # =========== Invitation Context ============

    @action("invitation-status-set", resources="invitation")
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
        user = stm.query('user', where=dict(
            email=data.email, status=UserStatus.ACTIVE), limit=1)
        user_id = None if not user else user[0]._id

        record = self.init_resource("invitation",
                                    serialize_mapping(data),
                                    organization_id=self.context.organization_id,
                                    profile_id=UUID_GENR(),
                                    user_id=user_id,
                                    token=secrets.token_urlsafe(16),
                                    status=InvitationStatus.PENDING,
                                    expires_at=datetime.utcnow() + timedelta(days=data.duration)
                                    )
        await stm.insert(record)
        await self.set_invitation_status(record, InvitationStatus.PENDING, "Initial invitation sent")
        return {"_id": record._id}

    @action("invitation-resent", resources="invitation")
    async def resend_invitation(self, stm, /):
        invitation = self.rootobj
        updates = {
            "token": secrets.token_urlsafe(16),
            "status": InvitationStatus.PENDING,
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        await stm.update(invitation, **updates)
        await self.set_invitation_status(invitation, InvitationStatus.PENDING, "Invitation resent")
        return {"_id": invitation._id, "resend": True}

    @action("invitation-canceled", resources="invitation")
    async def cancel_invitation(self, stm, /):
        invitation = self.rootobj
        await stm.update(invitation, status=InvitationStatus.CANCELED)
        await self.set_invitation_status(invitation, InvitationStatus.CANCELED, "Invitation canceled")
        return {"_id": invitation._id, "canceled": True}

    @action("invitation-accepted", resources="invitation")
    async def accept_invitation(self, stm, /):
        invitation = self.rootobj
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError("Only PENDING invitations can be accepted.")
        await stm.update(invitation, status=InvitationStatus.ACCEPTED, user_id=self.context.user_id)
        await self.set_invitation_status(invitation, InvitationStatus.ACCEPTED, "Invitation accepted")
        return {"_id": invitation._id, "accepted": True}

    @action("invitation-rejected", resources="invitation")
    async def reject_invitation(self, stm, /):
        invitation = self.rootobj

        if invitation.status != InvitationStatus.PENDING:
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

    @action("profile-updated", resources="profile")
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

    @action("role-assigned-to-profile", resources="profile")
    async def assign_role_to_profile(self, stm, /, data):
        role = await stm.fetch('ref--system-role', data.role_id)
        if await stm.find_all("profile-role", where=dict(
            profile_id=self.aggroot.identifier,
            role_id=data.role_id,
            role_source=data.role_source
        )):
            raise ValueError(f"{role.key} already assigned to profile!")

        record = self.init_resource("profile-role",
                                    serialize_mapping(data),
                                    _id=UUID_GENR(),
                                    profile_id=self.aggroot.identifier,
                                    role_key=role.key
                                    )
        await stm.insert(record)
        return record

    @action("role-revoked-from-profile", resources="profile")
    async def revoke_role_from_profile(self, stm, /, data):
        item = await stm.fetch('profile-role', data.profile_role_id, profile_id=self.aggroot.identifier)
        await stm.invalidate_one('profile-role', item._id)

    @action("role-cleared-from-profile", resources="profile")
    async def clear_all_role_from_profile(self, stm, /):
        roles = await stm.find_all('profile-role', where=dict(profile_id=self.aggroot.identifier))
        for role in roles:
            await stm.invalidate_one('profile-role', role._id)

    # =========== Group Context ==========
    @action("group-assigned-to-profile", resources="profile")
    async def assign_group_to_profile(self, stm, /, data):
        group = await stm.fetch('group', data.group_id)
        if not group:
            raise ValueError(f"Group with id {data.group_id} not found!")

        # Check if group is already assigned
        if await stm.find_all("profile-group", where=dict(
            profile_id=data.profile_id or self.aggroot.identifier,
            group_id=data.group_id
        )):
            raise ValueError(
                f"Group {group.name} already assigned to profile!")

        record = self.init_resource("profile-group",
                                    _id=UUID_GENR(),
                                    group_id=data.group_id,
                                    profile_id=data.profile_id or self.aggroot.identifier
                                    )
        await stm.insert(record)
        return record

    @action("group-revoked-from-profile", resources="profile")
    async def revoke_group_from_profile(self, stm, /, data):
        item = await stm.fetch('profile-group', data.profile_group_id)
        if not item:
            raise ValueError(
                f"Profile-group association with id {data.profile_group_id} not found!")
        await stm.invalidate_one('profile-group', item._id)

    @action("group-cleared-from-profile", resources="profile")
    async def clear_all_group_from_profile(self, stm, /):
        groups = await stm.find_all('profile-group', where=dict(profile_id=self.aggroot.identifier))
        for group in groups:
            await stm.invalidate_one('profile-group', group._id)

    @action("group-created", resources="group")
    async def create_group(self, stm, /, data):
        record = self.init_resource(
            "group",
            serialize_mapping(data),
            _id=self.aggroot.identifier,
            _txt=None  # TSVECTOR will be handled by database trigger
        )
        await stm.insert(record)
        return record

    @action("group-updated", resources="group")
    async def update_group(self, stm, /, data):
        item = self.rootobj
        await stm.update(item, **serialize_mapping(data.updates))
        return item

    @action("group-deleted", resources="group")
    async def delete_group(self, stm, /):
        # First remove all profile associations
        groups = await stm.find_all('profile-group', where=dict(group_id=self.aggroot.identifier))
        for group in groups:
            await stm.invalidate_one('profile-group', group._id)

        # Then delete the group
        await stm.invalidate_one('group', self.aggroot.identifier)
