"""
RFX IDM Domain Aggregate - Business Logic and State Management

This aggregate implements the domain model for the RFX IDM system, managing:
- User lifecycle (activation, deactivation, synchronization with Keycloak)
- Organization management (creation, role assignments, status tracking)
- Invitation workflows (send, accept, reject, cancel)
- Profile management (creation, updates, role/group assignments)
- Group management (creation, member assignments, permissions)

Uses the Fluvius framework's aggregate pattern with action decorators for
event sourcing and state management. All operations include audit trails
and status history tracking.
"""

import secrets
from datetime import datetime, timedelta
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, UUID_GENR
from .types import OrganizationStatusEnum, ProfileStatusEnum, UserStatusEnum, InvitationStatusEnum


class IDMAggregate(Aggregate):
    """
    Main aggregate for RFX IDM domain operations.
    Handles business logic for users, organizations, profiles, invitations, and groups.
    """

    # ==========================================================================
    # STATUS TRACKING HELPERS
    # ==========================================================================

    async def set_org_status(self, org, status, note=None):
        """Track organization status changes with audit trail."""
        record = self.init_resource("organization_status",
                                    organization_id=org._id,
                                    src_state=org.status,
                                    dst_state=status,
                                    note=note
                                    )
        await self.statemgr.insert(record)

    async def set_profile_status(self, profile, status, note=None):
        """Track profile status changes with audit trail."""
        record = self.init_resource("profile_status",
                                    profile_id=profile._id,
                                    src_state=profile.status,
                                    dst_state=status,
                                    note=note
                                    )
        await self.statemgr.insert(record)

    async def set_user_status(self, user, status, note=None):
        """Track user status changes with audit trail."""
        record = self.init_resource("user_status",
                                    user_id=user._id,
                                    src_state=user.status,
                                    dst_state=status,
                                    note=note
                                    )
        await self.statemgr.insert(record)

    # ==========================================================================
    # USER OPERATIONS
    # ==========================================================================

    # =========== User Context ============
    @action("user-action-tracked", resources="user")
    async def track_user_action(self, data):
        """Track user actions (e.g., password reset, email verification) for audit purposes."""
        for _action in data.actions:
            record = self.init_resource('user_action', dict(
                user_id=self.context.user_id,
                action=_action,
                name=_action
            ))
            await self.statemgr.insert(record)

    @action("user-created", resources="user")
    async def create_user(self, data):
        """Create new user with initial NEW status and verified email."""
        # Use provided _id (from Keycloak) if available, otherwise generate new one
        user_id = data.get("_id", UUID_GENR())

        record = self.init_resource(
            "user",
            data,
            _id=user_id,
            status='NEW',
            verified_email=data.get("verified_email") or data.get("telecom__email"),
        )
        await self.statemgr.insert(record)
        await self.set_user_status(record, record.status)
        return record

    @action("user-updated", resources="user")
    async def update_user(self, data):
        """Update user information and track status changes."""
        item = self.rootobj
        await self.statemgr.update(item, **serialize_mapping(data))
        if getattr(data, "status", None) and item.status != data.status:
            await self.set_user_status(item, data.status)
        return item

    @action("user-synced", resources="user")
    async def sync_user(self, data):
        """
        Synchronize user data from Keycloak and manage required actions.
        Handles action lifecycle (pending -> completed) based on Keycloak state.
        """
        user = self.rootobj
        await self.statemgr.update(user, **data.user_data)

        # Handle user actions
        if data.sync_actions:
            # Get current pending actions from database
            current_actions = await self.statemgr.find_all('user_action', where=dict(
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
                        record = self.init_resource('user_action', dict(
                            user_id=user._id,
                            action=action,
                            name=action,
                            status='PENDING'
                        ))
                        await self.statemgr.insert(record)

                # Any current actions not in required_actions should be marked as completed
                for action in current_actions:
                    if action._id not in processed_actions:
                        await self.statemgr.update(action, status='COMPLETED')
            else:
                # If no required actions, mark all pending actions as completed
                for action in current_actions:
                    await self.statemgr.update(action, status='COMPLETED')

        return user

    @action("user-deactivated", resources="user")
    async def deactivate_user(self, data=None):
        """Deactivate user account and record status change."""
        item = self.rootobj
        await self.statemgr.update(item, status=UserStatusEnum.DEACTIVATED.value)
        await self.set_user_status(item, UserStatusEnum.DEACTIVATED.value)

    @action("user-activated", resources="user")
    async def activate_user(self, data=None):
        """Activate user account and record status change."""
        item = self.rootobj
        await self.statemgr.update(item, status=UserStatusEnum.ACTIVE.value)
        await self.set_user_status(item, UserStatusEnum.ACTIVE.value)

    @action("user-synced", resources="user")
    async def sync_user(self, data):
        """
        Synchronize user data from Keycloak and manage required actions.
        Handles action lifecycle (pending -> completed) based on Keycloak state.
        """
        user = self.rootobj
        await self.statemgr.update(user, **data.user_data)

        # Handle user actions
        if data.sync_actions:
            # Get current pending actions from database
            current_actions = await self.statemgr.find_all('user_action', where=dict(
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
                        record = self.init_resource('user_action', dict(
                            user_id=user._id,
                            action=action,
                            name=action,
                            status='PENDING'
                        ))
                        await self.statemgr.insert(record)

                # Any current actions not in required_actions should be marked as completed
                for action in current_actions:
                    if action._id not in processed_actions:
                        await self.statemgr.update(action, status='COMPLETED')
            else:
                # If no required actions, mark all pending actions as completed
                for action in current_actions:
                    await self.statemgr.update(action, status='COMPLETED')

        return user

    # ==========================================================================
    # ORGANIZATION OPERATIONS
    # ==========================================================================

    @action("organization-created", resources="organization")
    async def create_organization(self, data):
        """Create new organization with initial SETUP status."""

        record = self.init_resource(
            "organization",
            data,
            _id=self.aggroot.identifier,
            status='NEW'
        )
        await self.statemgr.insert(record)
        await self.set_org_status(record, record.status)
        return record


    @action("organization-updated", resources="organization")
    async def update_organization(self, data):
        """Update organization details and track status changes."""
        item = self.rootobj
        await self.statemgr.update(item, **serialize_mapping(data))
        if getattr(data, "status", None) and item.status != data.status:
            await self.set_org_status(item, data.status)

        return item

    @action("organization-activated", resources="organization")
    async def activate_organization(self, data=None):
        """Reactivate organization and record status change."""
        item = self.rootobj
        await self.statemgr.update(item, status=OrganizationStatusEnum.ACTIVE.value)
        await self.set_org_status(item, OrganizationStatusEnum.ACTIVE.value)

    @action("organization-deactivated", resources="organization")
    async def deactivate_organization(self, data=None):
        """Deactivate organization and record status change."""
        item = self.rootobj
        await self.statemgr.update(item, status=OrganizationStatusEnum.DEACTIVATED.value)
        await self.set_org_status(item, OrganizationStatusEnum.DEACTIVATED.value)

    @action("org-role-created", resources="organization")
    async def create_org_role(self, data):
        """Create custom role within organization."""
        record = self.init_resource("organization-role", data, _id=UUID_GENR(), organization_id=self.aggroot.identifier)
        await self.statemgr.insert(record)
        return {"role_id": record._id}

    @action("org-role-updated", resources="organization")
    async def update_org_role(self, data):
        """Update organization role permissions or details."""
        item = await self.statemgr.fetch('organization_role', data.role_id, organization_id=self.aggroot.identifier)
        await self.statemgr.update(item, **serialize_mapping(data.updates))
        return {"updated": True}

    @action("org-role-removed", resources="organization")
    async def remove_org_role(self, data):
        """Remove organization role and revoke from all profiles."""
        item = await self.statemgr.fetch('organization_role', data.role_id, organization_id=self.aggroot.identifier)
        await self.statemgr.invalidate_data("organization_role", item._id)
        return {"removed": True}

    @action("org-type-created", resources="organization")
    async def create_org_type(self, data):
        """Create new organization type."""
        record = self.init_resource("ref__organization_type", serialize_mapping(data), _id=UUID_GENR())
        await self.statemgr.insert(record)
        return {"org_type_id": record._id}

    @action("org-type-removed", resources="organization")
    async def remove_org_type(self, data):
        """Remove organization type."""
        key = data.get("key")
        item = await self.statemgr.exist('ref__organization_type', where=dict(key=key))
        if item is None:
            return {"message": "Organization type not found."}
        await self.statemgr.invalidate_data('ref__organization_type', item._id)
        return {"removed": True}


    # =========== Invitation Context ============

    @action("invitation-status-set", resources="invitation")
    async def set_invitation_status(self, invitation, new_status: InvitationStatusEnum):
        """Track invitation status changes with audit trail."""
        status_record = self.init_resource("invitation_status",
                                           invitation_id=invitation._id,
                                           src_state=invitation.status,
                                           dst_state=new_status.value,
                                           )
        await self.statemgr.insert(status_record)

    @action("invitation-sent", resources="invitation")
    async def send_invitation(self, data):
        email = data.get("email")
        duration = data.get("duration")
        message = data.get("message", "")
        user = await self.statemgr.exist("user", where=dict(verified_email=email))
        if not user:
            return {"error": f"User with email {email} not found."}
        invitation_record = dict(
            _id=UUID_GENR(),
            sender_id=self.context.user_id,
            organization_id=self.context.organization_id,
            user_id=user._id,
            email=email,
            token=secrets.token_urlsafe(48),
            status=InvitationStatusEnum.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=duration),
            message=message,
            duration=duration
        )
        record = self.init_resource("invitation", invitation_record)
        await self.statemgr.insert(record)
        await self.set_invitation_status(record, InvitationStatusEnum.PENDING)
        return {"_id": record._id}

    @action("invitation-resent", resources="invitation")
    async def resend_invitation(self):
        """Resend invitation with new token and extended expiry."""
        invitation = self.rootobj
        updates = {
            "token": secrets.token_urlsafe(48),
            "status": InvitationStatusEnum.PENDING,
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        await self.statemgr.update(invitation, **updates)
        await self.set_invitation_status(invitation, InvitationStatusEnum.PENDING)
        return {"_id": invitation._id, "resend": True}

    @action("invitation-revoked", resources="invitation")
    async def revoke_invitation(self):
        """Cancel pending invitation to prevent acceptance."""
        invitation = self.rootobj
        await self.statemgr.update(invitation, status=InvitationStatusEnum.REVOKED)
        await self.set_invitation_status(invitation, InvitationStatusEnum.REVOKED)
        return {"_id": invitation._id, "revoked": True}

    # ==========================================================================
    # PROFILE OPERATIONS
    # ==========================================================================

    @action("profile-created", resources=("organization", "profile"))
    async def create_profile(self, data):
        """Create user profile within organization. Generates unique profile with default ACTIVE status."""
        user_id = data.get("user_id", None)
        if user_id is None or user_id == self.context.user_id:
            return {"message": "Cannot create profile for current user."}
        existing_profiles = await self.statemgr.find_all("profile", where=dict(
            user_id=user_id,
            organization_id=self.context.organization_id,
            status=ProfileStatusEnum.ACTIVE
        ))
        if existing_profiles:
            return {"message": "Active profile already exists for user in this organization."}

        user = await self.statemgr.fetch('user', user_id)
        if not user:
            return {"message": f"User with id {user_id} not found."}

        record = self.init_resource(
            "profile",
            data,
            _id=UUID_GENR(),
            organization_id=self.context.organization_id,
            status=data.get("status", ProfileStatusEnum.ACTIVE),
        )
        await self.statemgr.insert(record)
        await self.set_profile_status(record, record.status)
        return record


    @action("profile-switched", resources="profile")
    async def switch_profile(self):
        """Switch active profile in user context."""
        profile_id = self.aggroot.identifier
        if profile_id == self.context.profile_id:
            return {"switched": False, "message": "Already using the specified profile."}

        profiles = await self.statemgr.find_all("profile", where=dict(
            user_id=self.context.user_id,
            status=ProfileStatusEnum.ACTIVE
        ))

        for profile in profiles:
            if profile._id == profile_id:
                await self.statemgr.update(profile, current_profile=True)
            else:
                await self.statemgr.update(profile, current_profile=False)

        return {"message": f"Switched to profile {profile_id}", "switched": True}

    @action("profile-created-in-org", resources=("profile", "organization"))
    async def create_profile_in_org(self, data):
        """Create user profile within organization with role assignment."""
        user_id = data.get("user_id", None)
        if user_id is None or user_id == self.context.user_id:
            return {"message": "Cannot create profile for current user."}
        existing_profiles = await self.statemgr.find_all("profile", where=dict(
            user_id=user_id,
            organization_id=data.get("organization_id"),
            status='ACTIVE'
        ))
        if existing_profiles:
            return {"message": "Active profile already exists for user in this organization."}

        user = await self.statemgr.fetch('user', user_id)
        if not user:
            return {"message": f"User with id {user_id} not found."}

        record = self.init_resource(
            "profile",
            **data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        await self.set_profile_status(record, record.status)


        return {"profile_id": str(record._id)}


    @action("profile-updated", resources="profile")
    async def update_profile(self, data):
        """Update profile information. Tracks status changes if updated."""
        item = self.rootobj
        await self.statemgr.update(item, **serialize_mapping(data))
        if getattr(data, "status", None) and item.status != data.status:
            await self.set_profile_status(item, data.status)

        return {"message": "Profile updated", "profile_id": item._id}

    @action("profile-deactivated", resources="profile")
    async def deactivate_profile(self, data=None):
        """Deactivate profile to prevent further access."""
        item = self.rootobj
        await self.statemgr.update(item, status=ProfileStatusEnum.DEACTIVATED.value)
        await self.set_profile_status(item, ProfileStatusEnum.DEACTIVATED.value)

    @action("profile-activated", resources="profile")
    async def activate_profile(self, data=None):
        """Activate profile to allow access."""
        item = self.rootobj
        await self.statemgr.update(item, status=ProfileStatusEnum.ACTIVE.value)
        await self.set_profile_status(item, ProfileStatusEnum.ACTIVE.value)

    @action("role-assigned-to-profile", resources=("organization", "profile"))
    async def assign_role_to_profile(self, data):
        """Assign system role to profile. Prevents duplicate role assignments."""
        role_key = data.get("role_key", "VIEWER")
        profile_id = data.get("profile_id", self.aggroot.identifier)

        role = await self.statemgr.exist('ref__system_role', where=dict(key=role_key))

        profile_role = await self.statemgr.exist('profile_role', where=dict(
            profile_id=profile_id,
        ))
        if not profile_role:
            record = self.init_resource("profile_role", **data, role_id=role._id, _id=UUID_GENR())
            await self.statemgr.insert(record)
            return

        if profile_role.role_key == role_key:
            raise ValueError(f"Role {role_key} already assigned to profile.")
        else:
            await self.statemgr.update(profile_role, role_key=role_key, role_id=role._id)
            raise ValueError(f"Profile role updated to {role_key}.")

    @action("role-revoked-from-profile", resources="profile")
    async def revoke_role_from_profile(self, data):
        """Revoke specific role from profile."""
        profile_role_id = data.get("profile_role_id")
        item = await self.statemgr.fetch('profile_role', profile_role_id, profile_id=self.aggroot.identifier)
        if not item:
            return {"message": f"Profile role with id {profile_role_id} not found!"}
        await self.statemgr.invalidate_data('profile_role', item._id)

    @action("role-cleared-from-profile", resources="profile")
    async def clear_all_role_from_profile(self):
        """Remove all roles assigned to profile."""
        roles = await self.statemgr.find_all('profile_role', where=dict(profile_id=self.aggroot.identifier))
        for role in roles:
            await self.statemgr.invalidate_data('profile_role', role._id)

    # ==========================================================================
    # GROUP OPERATIONS
    # ==========================================================================

    @action("group-assigned-to-profile", resources="profile")
    async def assign_group_to_profile(self, data):
        """Assign profile to group. Validates group exists and prevents duplicates."""
        group = await self.statemgr.fetch('group', data.group_id)
        if not group:
            raise ValueError(f"Group with id {data.group_id} not found!")

        # Check if group is already assigned
        if await self.statemgr.find_all("profile_group", where=dict(
            profile_id=data.profile_id or self.aggroot.identifier,
            group_id=data.group_id
        )):
            raise ValueError(
                f"Group {group.name} already assigned to profile!")

        record = self.init_resource("profile_group",
                                    _id=UUID_GENR(),
                                    group_id=data.group_id,
                                    profile_id=data.profile_id or self.aggroot.identifier
                                    )
        await self.statemgr.insert(record)
        return record

    @action("group-revoked-from-profile", resources="profile")
    async def revoke_group_from_profile(self, data):
        item = await self.statemgr.fetch('profile_group', data.profile_group_id)
        if not item:
            raise ValueError(
                f"Profile_group association with id {data.profile_group_id} not found!")
        await self.statemgr.invalidate_data('profile_group', item._id)

    @action("group-cleared-from-profile", resources="profile")
    async def clear_all_group_from_profile(self):
        groups = await self.statemgr.find_all('profile_group', where=dict(profile_id=self.aggroot.identifier))
        for group in groups:
            await self.statemgr.invalidate_data('profile_group', group._id)

    @action("group-created", resources="group")
    async def create_group(self, data):
        record = self.init_resource(
            "group",
            serialize_mapping(data),
            _id=self.aggroot.identifier,
            _txt=None  # TSVECTOR will be handled by database trigger
        )
        await self.statemgr.insert(record)
        return record

    @action("group-updated", resources="group")
    async def update_group(self, data):
        item = self.rootobj
        await self.statemgr.update(item, **serialize_mapping(data.updates))
        return item

    @action("group-deleted", resources="group")
    async def delete_group(self):
        # First remove all profile associations
        groups = await self.statemgr.find_all('profile_group', where=dict(group_id=self.aggroot.identifier))
        for group in groups:
            await self.statemgr.invalidate_data('profile_group', group._id)

        # Then delete the group
        await self.statemgr.invalidate_data('group', self.aggroot.identifier)
