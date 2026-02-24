"""
RFX User Domain Aggregate - Business Logic and State Management

This aggregate implements the domain model for the RFX User system, managing:
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
from . import config, logger


class UserProfileAggregate(Aggregate):
    """
    Main aggregate for RFX User domain operations.
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
    # @action("user-action-tracked", resources="user")
    # async def track_user_action(self, data):
    #     """Track user actions (e.g., password reset, email verification) for audit purposes."""
    #     for _action in data.actions:
    #         record = self.init_resource('user_action', dict(
    #             user_id=self.context.user_id,
    #             action=_action,
    #             name=_action
    #         ))
    #         await self.statemgr.insert(record)

    # @action("user-updated", resources="user")
    # async def update_user(self, data):
    #     """Update user information and track status changes."""
    #     item = self.rootobj
    #     await self.statemgr.update(item, **serialize_mapping(data))
    #     if getattr(data, "status", None) and item.status != data.status:
    #         await self.set_user_status(item, data.status)
    #     return item

    # @action("user-deactivated", resources="user")
    # async def deactivate_user(self, data=None):
    #     """Deactivate user account and record status change."""
    #     item = self.rootobj
    #     await self.statemgr.update(item, status=UserStatusEnum.DEACTIVATED)
    #     await self.set_user_status(item, UserStatusEnum.DEACTIVATED)

    # @action("user-activated", resources="user")
    # async def activate_user(self, data=None):
    #     """Activate user account and record status change."""
    #     item = self.rootobj
    #     await self.statemgr.update(item, status=UserStatusEnum.ACTIVE)
    #     await self.set_user_status(item, UserStatusEnum.ACTIVE)

    # @action("user-synced", resources="user")
    # async def sync_user(self, data):
    #     """
    #     Synchronize user data from Keycloak and manage required actions.
    #     Handles action lifecycle (pending -> completed) based on Keycloak state.
    #     """
    #     user = self.rootobj
    #     await self.statemgr.update(user, **data.user_data)

    #     # Handle user actions
    #     if data.sync_actions:
    #         # Get current pending actions from database
    #         current_actions = await self.statemgr.find_all('user_action', where=dict(
    #             user_id=user._id,
    #             status='PENDING'
    #         ))

    #         # If there are required actions from Keycloak, update or create them
    #         if data.required_actions:
    #             # Track which actions we've seen
    #             processed_actions = set()

    #             for action in data.required_actions:
    #                 # Try to find existing action
    #                 existing = next(
    #                     (a for a in current_actions if a.action == action), None)

    #                 if existing:
    #                     # Action already exists, mark as seen
    #                     processed_actions.add(existing._id)
    #                 else:
    #                     # Create new action record
    #                     record = self.init_resource('user_action', dict(
    #                         user_id=user._id,
    #                         action=action,
    #                         name=action,
    #                         status='PENDING'
    #                     ))
    #                     await self.statemgr.insert(record)

    @action("user-action-recorded", resources=("user", "user_action"))
    async def record_user_action(self, data):
        user = self.rootobj
        action_type = data.get("action_type")

        record = self.init_resource(
            "user_action",
            name=f"{action_type.lower().replace('_', '-')}-action",
            action_type=action_type,
            status='PENDING',
            user_id=user._id,
            action_data=data.get("action_data", {}),
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action("user-action-updated", resources=("user", "user_action"))
    async def update_user_action(self, data):
        user = self.rootobj
        action_id = data.get("action_id")

        user_action = await self.statemgr.fetch("user_action", action_id)
        if not user_action:
            raise ValueError("Invalid action ID")
        if getattr(user_action.status, "value", user_action.status) != "PENDING":
            raise ValueError("Action is no longer pending")
        if str(user_action.user_id) != str(user._id):
            raise ValueError("Action does not belong to this user")

        action_data = user_action.action_data or {}
        action_data.update(data.get("action_data", {}))

        await self.statemgr.update(user_action, action_data=action_data)
        return user_action

    #             # Any current actions not in required_actions should be marked as completed
    #             for action in current_actions:
    #                 if action._id not in processed_actions:
    #                     await self.statemgr.update(action, status='COMPLETED')
    #         else:
    #             # If no required actions, mark all pending actions as completed
    #             for action in current_actions:
    #                 await self.statemgr.update(action, status='COMPLETED')

    #     return user

    # ==========================================================================
    # ORGANIZATION OPERATIONS
    # ==========================================================================

    # @action("organization-created", resources="organization")
    # async def create_organization(self, data):
    #     """Create new organization with initial SETUP status."""

    #     record = self.init_resource(
    #         "organization",
    #         serialize_mapping(data),
    #         _id=self.aggroot.identifier,
    #         status=getattr(data, "status", "SETUP")
    #     )
    #     await self.statemgr.insert(record)
    #     await self.set_org_status(record, record.status)
    #     return record


    @action("organization-updated", resources="organization")
    async def update_organization(self, data):
        """Update organization details and track status changes."""
        item = self.rootobj
        await self.statemgr.update(item, **serialize_mapping(data))
        if getattr(data, "status", None) and item.status != data.status:
            await self.set_org_status(item, data.status)

        return item

    # @action("organization-deactivated", resources="organization")
    # async def deactivate_organization(self, data=None):
    #     """Deactivate organization and record status change."""
    #     item = self.rootobj
    #     await self.statemgr.update(item, status=OrganizationStatusEnum.DEACTIVATED)
    #     await self.set_org_status(item, OrganizationStatusEnum.DEACTIVATED)

    # @action("org-role-created", resources="organization")
    # async def create_org_role(self, data):
    #     """Create custom role within organization."""
    #     record = self.init_resource("organization-role", data, _id=UUID_GENR(), organization_id=self.aggroot.identifier)
    #     await self.statemgr.insert(record)
    #     return {"role_id": record._id}

    # @action("org-role-updated", resources="organization")
    # async def update_org_role(self, data):
    #     """Update organization role permissions or details."""
    #     item = await self.statemgr.fetch('organization_role', data.role_id, organization_id=self.aggroot.identifier)
    #     await self.statemgr.update(item, **serialize_mapping(data.updates))
    #     return {"updated": True}

    # @action("org-role-removed", resources="organization")
    # async def remove_org_role(self, data):
    #     """Remove organization role and revoke from all profiles."""
    #     item = await self.statemgr.fetch('organization_role', data.role_id, organization_id=self.aggroot.identifier)
    #     await self.statemgr.invalidate_data("organization_role", item._id)
    #     return {"removed": True}

    # @action("org-type-created", resources="organization")
    # async def create_org_type(self, data):
    #     """Create new organization type."""
    #     record = self.init_resource("ref__organization_type", serialize_mapping(data), _id=UUID_GENR())
    #     await self.statemgr.insert(record)
    #     return {"org_type_id": record._id}

    # @action("org-type-removed", resources="organization")
    # async def remove_org_type(self, data):
    #     """Remove organization type."""
    #     key = data.get("key")
    #     item = await self.statemgr.exist('ref__organization_type', where=dict(key=key))
    #     if item is None:
    #         return {"message": "Organization type not found."}
    #     await self.statemgr.invalidate_data('ref__organization_type', item._id)
    #     return {"removed": True}


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
        realm = data.get("realm")
        realm_exist = await self.statemgr.exist("realm", where=dict(key=realm))
        if not realm_exist:
            raise ValueError(f"realm {realm} is not existed")
        user = await self.statemgr.exist("user", where=dict(verified_email=email))
        if not user:
            raise ValueError(f"User with email {email} not found!")
        exist_profile = self.statemgr.exist(
            "profile",
            realm=realm,
            organization_id=self.context.organization_id,
            user_id=user_id,
            status='ACTIVE'
        )
        if exist_profile:
            raise ValueError(f"User already have an ACTIVE profile in the current organization")

        # Check for existing pending invitations
        existing_invitations = await self.statemgr.find_all(
            "invitation",
            where=dict(
                user_id=user._id,
                organization_id=self.context.organization_id,
                realm=realm,
                status=InvitationStatusEnum.PENDING.value
            )
        )

        current_time = datetime.utcnow()
        for inv in existing_invitations:
            if inv.expires_at and inv.expires_at > current_time:
                 raise ValueError("User already has a pending invitation for this organization and realm.")

        # Rate limit check
        window_minutes = config.RATE_LIMIT_WINDOW_MINUTES
        max_requests = config.INVITATION_MAX_REQUESTS_PER_WINDOW
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)

        # We need to fetch all invitations for this user to check the rate limit
        # reusing existing_invitations is not enough because it only fetches PENDING ones
        all_recent_invitations = await self.statemgr.find_all(
            "invitation",
            where=dict(
                sender_id=self.context.user_id,
                **{"_created.gt": window_start}
            )
        )

        recent_count = len(all_recent_invitations)
        if recent_count >= max_requests:
            raise ValueError(f"Too many invitations sent. Please wait {window_minutes} minutes.")

        invitation_record = dict(
            _id=UUID_GENR(),
            sender_id=self.context.user_id,
            organization_id=self.context.organization_id,
            user_id=user._id,
            email=email,
            token=secrets.token_urlsafe(48),
            status=InvitationStatusEnum.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(days=duration),
            message=message,
            duration=duration,
            realm=realm,
        )

        record = self.init_resource("invitation", invitation_record)
        await self.statemgr.insert(record)
        await self.set_invitation_status(record, InvitationStatusEnum.PENDING)


        # Send invitation email
        try:
            context = self.context
            notify_client = getattr(self.context.service_proxy, config.SERVICE_CLIENT, None)
            if not notify_client:
                raise RuntimeError("Notification service client is not found")

            # Fetch organization name
            org = await self.statemgr.fetch("organization", self.context.organization_id)
            org_name = org.name if org else "Organization"

            # Construct invitation links
            base_url = config.API_BASE_URL
            accept_link = f"{base_url}/{config.NAMESPACE}.accept-invitation/{record._id}?token={record.token}"
            reject_link = f"{base_url}/{config.NAMESPACE}.reject-invitation/{record._id}?token={record.token}"

            await notify_client.send(
                "rfx-notify:send-notification",
                command="send-notification",
                resource="notification",
                payload={
                    "channel": "EMAIL",
                    "recipients": [record.email],
                    "template_key": "org-invitation-default",
                    "content_type": "HTML",
                    "template_data": {
                        "organization_name": org_name,
                        "accept_link": accept_link,
                        "reject_link": reject_link,
                        "duration_days": record.duration,
                        "message": record.message or "",
                    },
                },
                identifier=UUID_GENR(),
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id) if context.user_id else None,
                        "profile_id": str(context.profile_id) if context.profile_id else None,
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    },
                    "source": "rfx-user",
                },
            )
        except Exception as e:
            logger.error(f"Failed to send invitation email: {e}")

        return {"_id": record._id, "token": record.token}

    @action("invitation-resent", resources="invitation")
    async def resend_invitation(self):
        """Resend invitation with new token and extended expiry."""
        invitation = self.rootobj
        updates = {
            "token": secrets.token_urlsafe(48),
            "status": InvitationStatusEnum.PENDING.value,
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        await self.statemgr.update(invitation, **updates)
        await self.set_invitation_status(invitation, InvitationStatusEnum.PENDING)

        # Resend invitation email
        try:
            context = self.context
            notify_client = getattr(self.context.service_proxy, config.SERVICE_CLIENT, None)
            if not notify_client:
                raise RuntimeError("Notification service client is not found")

            # Fetch organization name
            org = await self.statemgr.fetch("organization", self.context.organization_id)
            org_name = org.name if org else "Organization"

            # Construct invitation links with updated token
            base_url = config.API_BASE_URL
            accept_link = f"{base_url}/{config.NAMESPACE}.accept-invitation/{invitation._id}?token={invitation.token}"
            reject_link = f"{base_url}/{config.NAMESPACE}.reject-invitation/{invitation._id}?token={invitation.token}"

            await notify_client.send(
                "rfx-notify:send-notification",
                command="send-notification",
                resource="notification",
                payload={
                    "channel": "EMAIL",
                    "recipients": [invitation.email],
                    "template_key": "org-invitation-default",
                    "content_type": "HTML",
                    "template_data": {
                        "organization_name": org_name,
                        "accept_link": accept_link,
                        "reject_link": reject_link,
                        "duration_days": invitation.duration,
                        "message": invitation.message or "",
                    },
                },
                identifier=UUID_GENR(),
                _headers={},
                _context={
                    "audit": {
                        "user_id": str(context.user_id) if context.user_id else None,
                        "profile_id": str(context.profile_id) if context.profile_id else None,
                        "organization_id": str(context.organization_id),
                        "realm": context.realm,
                    },
                    "source": "rfx-user",
                },
            )
        except Exception as e:
            logger.error(f"Failed to resend invitation email: {e}")

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
        user_id = data.get("user_id")
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
        await self.statemgr.update(
            item,
            status=ProfileStatusEnum.DEACTIVATED.value,
            current_profile=False
        )
        await self.set_profile_status(item, ProfileStatusEnum.DEACTIVATED.value)



    # @action("role-assigned-to-profile", resources=("organization", "profile"))
    # async def assign_role_to_profile(self, data):
    #     """Assign system role to profile. Supports multiple roles with constraints."""
    #     role_key = data.get("role_key", "VIEWER")
    #     profile_id = data.get("profile_id", str(self.aggroot.identifier))

    #     # Fetch the system role
    #     role = await self.statemgr.exist('ref__system_role', where=dict(key=role_key))
    #     if not role:
    #         raise ValueError(f"System role '{role_key}' does not exist.")

    #     # Get all existing roles for this profile
    #     existing_roles = await self.statemgr.find_all('profile_role', where=dict(
    #         profile_id=profile_id,
    #     ))

    #     # Check if profile has ADMIN or OWNER role - they can't have additional roles
    #     for existing_role in existing_roles:
    #         if existing_role.role_key in ('ADMIN', 'OWNER'):
    #             raise ValueError(f"Profile with {existing_role.role_key} role cannot be assigned additional roles.")

    #     # Check if trying to assign ADMIN or OWNER to a profile that already has other roles
    #     if role_key in ('ADMIN', 'OWNER') and existing_roles:
    #         raise ValueError(f"Cannot assign {role_key} role to a profile that already has other roles.")

    #     # Check if trying to assign the same role (prevent duplicates)
    #     for existing_role in existing_roles:
    #         if existing_role.role_key == role_key:
    #             raise ValueError(f"Role {role_key} already assigned to profile.")

    #     # If assigning OWNER, check no other OWNER exists in org
    #     if role_key == 'OWNER':
    #         all_owner_roles = await self.statemgr.find_all('profile_role', where=dict(
    #             role_key='OWNER'
    #         ))
    #         # Check if any owner is in the same organization
    #         for owner_role in all_owner_roles:
    #             owner_profile = await self.statemgr.fetch('profile', owner_role.profile_id)
    #             if owner_profile and owner_profile.organization_id == self.context.organization_id:
    #                 raise ValueError("Organization can have only one OWNER role assigned.")

    #     # Create new role assignment (only add, never update)
    #     record = self.init_resource("profile_role", profile_id=profile_id, role_key=role_key, role_id=role._id, _id=UUID_GENR())
    #     await self.statemgr.insert(record)
    #     return {"message": f"Role {role_key} assigned to profile"}


    @action("profile-roles-updated", resources=("organization", "profile"))
    async def update_profile_roles(self, data):
        """Sync profile roles with the provided list of role keys."""
        role_keys = data.get("role_keys", [])
        profile_id = data.get("profile_id", str(self.aggroot.identifier))

        if not role_keys:
             raise ValueError("Role keys list cannot be empty.")

        # Unique keys
        role_keys = list(set(role_keys))

        # Validation for exclusive roles
        if ('ADMIN' in role_keys or 'OWNER' in role_keys) and len(role_keys) > 1:
            raise ValueError("ADMIN or OWNER roles cannot be combined with other roles.")

        # Fetch all provided system roles
        system_roles = {}
        for key in role_keys:
            role = await self.statemgr.exist('ref__system_role', where=dict(key=key))
            if not role:
                raise ValueError(f"System role '{key}' does not exist.")
            system_roles[key] = role

        # Fetch existing profile roles
        existing_roles = await self.statemgr.find_all('profile_role', where=dict(
            profile_id=profile_id,
        ))
        existing_keys = {r.role_key for r in existing_roles}

        # Calculate roles to add and remove
        to_add = [k for k in role_keys if k not in existing_keys]
        to_remove = [r for r in existing_roles if r.role_key not in role_keys]

        # Check OWNER constraints for new assignments
        if 'OWNER' in to_add:
            # Fetch the profile we're assigning to, to get its organization
            current_profile = await self.statemgr.fetch('profile', profile_id)

            all_owner_roles = await self.statemgr.find_all('profile_role', where=dict(
                role_key='OWNER'
            ))
            for owner_role in all_owner_roles:
                # Ignore self if already owner (limit handled by to_add check)
                if owner_role.profile_id != profile_id:
                    owner_profile = await self.statemgr.fetch('profile', owner_role.profile_id)
                    # Use the profile's organization_id, not context
                    if (owner_profile and
                        owner_profile.organization_id == current_profile.organization_id and
                        owner_profile.status == "ACTIVE"):
                        raise ValueError(f"Organization can have only one OWNER role assigned. {owner_profile.name__family} {owner_profile.name__given}")

        # Perform updates
        for role_record in to_remove:
            await self.statemgr.invalidate_data('profile_role', role_record._id)

        for key in to_add:
            role = system_roles[key]
            record = self.init_resource("profile_role",
                                      profile_id=profile_id,
                                      role_key=key,
                                      role_id=role._id,
                                      _id=UUID_GENR())
            await self.statemgr.insert(record)

        return {"message": "Profile roles updated", "added": to_add, "removed": [r.role_key for r in to_remove]}


    @action("role-revoked-from-profile", resources="profile")
    async def revoke_role_from_profile(self, data):
        """Revoke specific role from profile. Cannot revoke OWNER/ADMIN or last remaining role."""
        profile_role_id = data.get("profile_role_id")
        item = await self.statemgr.fetch('profile_role', profile_role_id, profile_id=self.aggroot.identifier)
        if not item:
            raise ValueError(f"Profile role with id {profile_role_id} not found!")

        # Cannot revoke OWNER or ADMIN roles
        if item.role_key in ('OWNER'):
            raise ValueError(f"Cannot revoke {item.role_key} role from profile.")

        # Check if this is the last role - profile must have at least one role
        all_roles = await self.statemgr.find_all('profile_role', where=dict(profile_id=self.aggroot.identifier))
        if len(all_roles) <= 1:
            raise ValueError("Cannot revoke the last role from profile. Profile must have at least one role.")

        await self.statemgr.invalidate_data('profile_role', item._id)
        return {"message": f"Role {item.role_key} revoked from profile"}


    @action("role-cleared-from-profile", resources="profile")
    async def clear_all_role_from_profile(self):
        """Remove all roles assigned to profile. Cannot clear OWNER/ADMIN roles."""
        roles = await self.statemgr.find_all('profile_role', where=dict(profile_id=self.aggroot.identifier))

        # Check if any role is OWNER or ADMIN
        for role in roles:
            if role.role_key in ('OWNER', 'ADMIN'):
                raise ValueError(f"Cannot clear roles: Profile has {role.role_key} role which cannot be removed.")

        # Clear all roles
        for role in roles:
            await self.statemgr.invalidate_data('profile_role', role._id)

        return {"message": "All roles cleared from profile"}

    @action("profile-deactivated", resources="profile")
    async def deactivate_profile(self, data=None):
        """Deactivate profile to prevent further access."""
        item = self.rootobj
        await self.statemgr.update(
            item,
            status=ProfileStatusEnum.DEACTIVATED.value,
            current_profile=False
        )
        await self.set_profile_status(item, ProfileStatusEnum.DEACTIVATED.value)

    @action("profile-activated", resources="profile")
    async def activate_profile(self, data=None):
        """Activate profile to allow access."""
        item = self.rootobj

        # Check for existing active profile in same org+realm
        existing_active = await self.statemgr.exist(
            "profile",
            where=dict(
                user_id=item.user_id,
                organization_id=item.organization_id,
                realm=item.realm,
                status=ProfileStatusEnum.ACTIVE.value
            )
        )

        if existing_active and existing_active._id != item._id:
            raise ValueError(
                "User already has an active profile in this organization and realm"
            )

        # Check if this profile has an OWNER role
        is_owner = await self.statemgr.exist('profile_role', where=dict(
            profile_id=item._id,
            role_key='OWNER'
        ))

        if is_owner:
            # Look for any other active profile in the org that is an OWNER
            all_active_profiles = await self.statemgr.find_all('profile', where=dict(
                organization_id=item.organization_id,
                status=ProfileStatusEnum.ACTIVE.value
            ))
            for p in all_active_profiles:
                if p._id == item._id:
                    continue
                other_owner = await self.statemgr.exist('profile_role', where=dict(
                    profile_id=p._id,
                    role_key='OWNER'
                ))
                if other_owner:
                    raise ValueError(f"Organization already has an owner: {p.name__family} {p.name__given}")

        await self.statemgr.update(
            item,
            status=ProfileStatusEnum.ACTIVE.value,
            current_profile=True
        )
        await self.set_profile_status(item, ProfileStatusEnum.ACTIVE.value)

    @action("profile-deleted", resources="profile")
    async def delete_profile(self):
        """Delete profile and clean up associated roles and groups."""
        current_profile = self.context.profile_id
        if current_profile == self.aggroot.identifier:
            raise ValueError("Cannot delete the currently active profile.")
        # First remove all role associations
        roles = await self.statemgr.find_all('profile_role', where=dict(profile_id=self.aggroot.identifier))
        for role in roles:
            if role.role_key == 'OWNER':
                raise ValueError("Cannot delete profile with OWNER role assigned.")
            await self.statemgr.invalidate_data('profile_role', role._id)

        # Then remove all group associations
        groups = await self.statemgr.find_all('profile_group', where=dict(profile_id=self.aggroot.identifier))
        for group in groups:
            await self.statemgr.invalidate_data('profile_group', group._id)

        # Finally delete the profile
        await self.statemgr.invalidate_data('profile', self.aggroot.identifier)


    # ==========================================================================
    # GROUP OPERATIONS
    # ==========================================================================

    # @action("group-assigned-to-profile", resources="profile")
    # async def assign_group_to_profile(self, data):
    #     """Assign profile to group. Validates group exists and prevents duplicates."""
    #     group = await self.statemgr.fetch('group', data.group_id)
    #     if not group:
    #         raise ValueError(f"Group with id {data.group_id} not found!")

    #     # Check if group is already assigned
    #     if await self.statemgr.find_all("profile_group", where=dict(
    #         profile_id=data.profile_id or self.aggroot.identifier,
    #         group_id=data.group_id
    #     )):
    #         raise ValueError(
    #             f"Group {group.name} already assigned to profile!")

    #     record = self.init_resource("profile_group",
    #                                 _id=UUID_GENR(),
    #                                 group_id=data.group_id,
    #                                 profile_id=data.profile_id or self.aggroot.identifier
    #                                 )
    #     await self.statemgr.insert(record)
    #     return record

    # @action("group-revoked-from-profile", resources="profile")
    # async def revoke_group_from_profile(self, data):
    #     item = await self.statemgr.fetch('profile_group', data.profile_group_id)
    #     if not item:
    #         raise ValueError(
    #             f"Profile_group association with id {data.profile_group_id} not found!")
    #     await self.statemgr.invalidate_data('profile_group', item._id)

    # @action("group-cleared-from-profile", resources="profile")
    # async def clear_all_group_from_profile(self):
    #     groups = await self.statemgr.find_all('profile_group', where=dict(profile_id=self.aggroot.identifier))
    #     for group in groups:
    #         await self.statemgr.invalidate_data('profile_group', group._id)

    # @action("group-created", resources="group")
    # async def create_group(self, data):
    #     record = self.init_resource(
    #         "group",
    #         serialize_mapping(data),
    #         _id=self.aggroot.identifier,
    #         _txt=None  # TSVECTOR will be handled by database trigger
    #     )
    #     await self.statemgr.insert(record)
    #     return record

    # @action("group-updated", resources="group")
    # async def update_group(self, data):
    #     item = self.rootobj
    #     await self.statemgr.update(item, **serialize_mapping(data.updates))
    #     return item

    # @action("group-deleted", resources="group")
    # async def delete_group(self):
    #     # First remove all profile associations
    #     groups = await self.statemgr.find_all('profile_group', where=dict(group_id=self.aggroot.identifier))
    #     for group in groups:
    #         await self.statemgr.invalidate_data('profile_group', group._id)

    #     # Then delete the group
    #     await self.statemgr.invalidate_data('group', self.aggroot.identifier)
