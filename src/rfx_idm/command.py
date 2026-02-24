from datetime import datetime
from fluvius.data import serialize_mapping, UUID_GENR
from fluvius.data.exceptions import ItemNotFoundError
from fluvius.error import BadRequestError

from datetime import datetime, timedelta
from .domain import IDMDomain
from .integration import kc_admin
from . import datadef, config
from rfx_user import config as userconf

processor = IDMDomain.command_processor
Command = IDMDomain.Command


# ============ User Context =============


DEFAULT_REALM_ACCESS = {
    "roles": [
        "offline_access",
        "default-roles-id.neucares.com",
        "uma_authorization",
    ]
}


DEFAULT_RESOURCE_ACCESS = {
    "account": {
        "roles": [
            "manage-account",
            "manage-account-links",
            "view-profile",
        ]
    }
}


class CreateUser(Command):
    """
    Create new user in Keycloak and local system.
    Establishes user account with initial settings and verification status.
    """

    class Meta:
        key = "create-user"
        resource_init = True
        resources = ("user",)
        tags = ["user", "create"]
        auth_required = True
        policy_required = True

    Data = datadef.CreateUserPayload

    async def _process(self, agg, stm, payload):
        email_verified = False
        if payload.email_verified is not None:
            email_verified = payload.email_verified
        elif payload.verified_email:
            email_verified = True

        # Prepare Keycloak user data
        kc_user_data = {
            "email": payload.email,
            "username": payload.username,
            "firstName": payload.first_name or "",
            "lastName": payload.last_name or "",
            "enabled": payload.is_active,
            "emailVerified": email_verified,
            "requiredActions": [],
        }

        # Add password credentials if provided
        if payload.password:
            kc_user_data["credentials"] = [
                {
                    "value": payload.password,
                    "temporary": False,
                    "type": "password",
                }
            ]
        else:
            # If no password provided, require user to update password
            kc_user_data["requiredActions"].append("UPDATE_PASSWORD")
        if not email_verified:
            kc_user_data["requiredActions"].append("VERIFY_EMAIL")

        # Create user in Keycloak
        try:
            kc_user = await kc_admin.create_user(kc_user_data)
        except BadRequestError as e:
            # Check if error is due to user already existing
            error_msg = str(e).lower()
            if "exists" not in error_msg:
                # Re-raise if it's a different error
                raise

            existing_users = await kc_admin.find_user(payload.username)

            # Filter for exact username match
            kc_user = None
            for user in existing_users:
                if user.username == payload.username:
                    kc_user = user
                    break

            # If not found by username, try by email
            if not kc_user and payload.email:
                existing_users = await kc_admin.find_user(payload.email)
                for user in existing_users:
                    if user.email == payload.email:
                        kc_user = user
                        break

            if not kc_user:
                raise

            update_payload = {
                "email": payload.email,
                "username": payload.username,
                "firstName": payload.first_name or "",
                "lastName": payload.last_name or "",
                "enabled": payload.is_active,
                "emailVerified": email_verified,
            }

            await kc_admin.update_user(kc_user.id, update_payload)

            if payload.password:
                await kc_admin.set_user_password(
                    kc_user.id, payload.password, temporary=False
                )

        realm_access = payload.realm_access or DEFAULT_REALM_ACCESS
        resource_access = payload.resource_access or DEFAULT_RESOURCE_ACCESS

        # Prepare local database user data with proper field mapping
        user_data = {
            "_id": kc_user.id,  # Use Keycloak user ID as primary key
            "username": payload.username,
            "active": payload.is_active,
            "is_super_admin": payload.is_superuser,
            # Name fields (with double underscore prefix)
            "name__given": payload.first_name,
            "name__family": payload.last_name,
            "name__middle": payload.middle_name,
            "name__prefix": payload.name_prefix,
            "name__suffix": payload.name_suffix,
            # Telecom fields (with double underscore prefix)
            "telecom__email": payload.email,
            "telecom__phone": payload.phone,
            # Verification fields
            "verified_email": (
                payload.verified_email or (payload.email if email_verified else None)
            ),
            "verified_phone": payload.verified_phone,
            # Access control (JSON fields)
            "realm_access": realm_access,
            "resource_access": resource_access,
        }
        # Create user in local database
        user = await agg.create_user(user_data)

        yield agg.create_response(serialize_mapping(user), _type="idm-response")


class UpdateUser(Command):
    """
    Update user attributes in Keycloak and local datastore.
    Synchronizes identity information, status, and verification metadata.
    """

    class Meta:
        key = "update-user"
        resources = ("user",)
        tags = ["user"]
        auth_required = True
        policy_required = True

    Data = datadef.UpdateUserPayload

    async def _process(self, agg, stm, payload):
        rootobj = agg.get_rootobj()
        user_id = rootobj._id

        # Build Keycloak update payload from provided fields
        kc_payload = {}
        if payload.email is not None:
            kc_payload["email"] = payload.email
        if payload.username is not None:
            kc_payload["username"] = payload.username
        if payload.first_name is not None:
            kc_payload["firstName"] = payload.first_name
        if payload.last_name is not None:
            kc_payload["lastName"] = payload.last_name
        if payload.is_active is not None:
            kc_payload["enabled"] = payload.is_active
        if payload.email_verified is not None:
            kc_payload["emailVerified"] = payload.email_verified
        if payload.verified_email is not None:
            kc_payload["emailVerified"] = bool(payload.verified_email)

        if kc_payload:
            await kc_admin.update_user(user_id, kc_payload)

        # Handle password change separately via Keycloak credential endpoint
        if payload.password:
            await kc_admin.set_user_password(user_id, payload.password, temporary=False)

        # Map payload fields to local datastore column names
        user_updates = {}

        def set_update(value, key, transform=None):
            if value is None:
                return
            user_updates[key] = transform(value) if transform else value

        set_update(payload.username, "username")
        set_update(payload.is_active, "active")
        set_update(payload.is_superuser, "is_super_admin")
        set_update(payload.first_name, "name__given")
        set_update(payload.last_name, "name__family")
        set_update(payload.middle_name, "name__middle")
        set_update(payload.name_prefix, "name__prefix")
        set_update(payload.name_suffix, "name__suffix")
        set_update(payload.email, "telecom__email")
        set_update(payload.phone, "telecom__phone")
        set_update(payload.verified_phone, "verified_phone")
        set_update(payload.realm_access, "realm_access")
        set_update(payload.resource_access, "resource_access")
        set_update(
            payload.status, "status", lambda v: v.value if hasattr(v, "value") else v
        )
        set_update(payload.last_verified_request, "last_verified_request")

        if payload.verified_email is not None:
            user_updates["verified_email"] = payload.verified_email
        elif payload.email_verified is True:
            user_updates["verified_email"] = payload.email or rootobj.telecom__email
        elif payload.email_verified is False:
            user_updates["verified_email"] = None

        updated_user = rootobj
        if user_updates:
            updated_user = await agg.update_user(user_updates)

        update_performed = (
            bool(kc_payload) or bool(payload.password) or bool(user_updates)
        )

        sync_requested = payload.sync_remote or payload.force_sync
        sync_only = sync_requested and not update_performed

        synced_user = None
        sync_status = None
        if sync_requested:
            synced_user, sync_status = await self._sync_from_keycloak(
                agg, force_sync=payload.force_sync, sync_actions=payload.sync_actions
            )

            if sync_status and sync_only:
                yield agg.create_response(sync_status, _type="idm-response")
                return

        result_user = synced_user or updated_user
        response_payload = serialize_mapping(result_user)

        if sync_status and not sync_only:
            response_payload["sync_status"] = sync_status

        yield agg.create_response(response_payload, _type="idm-response")

    async def _sync_from_keycloak(self, agg, force_sync: bool, sync_actions: bool):
        """Pull latest user info from Keycloak and update local state."""
        user = agg.get_rootobj()
        if not force_sync and getattr(user, "last_sync", None):
            elapsed = (datetime.utcnow() - user.last_sync).total_seconds()
            if elapsed < 300:
                return None, {"status": "skipped", "reason": "Recently synced"}

        user_id = user._id
        kc_user = await kc_admin.get_user(user_id)
        if not kc_user:
            raise ValueError(f"User {user_id} not found in Keycloak")

        user_data = {
            "name__family": kc_user.lastName,
            "name__given": kc_user.firstName,
            "telecom__email": kc_user.email,
            "username": kc_user.username,
            "active": kc_user.enabled,
            "realm_access": kc_user.realmRoles,
            "resource_access": kc_user.clientRoles,
            "verified_email": kc_user.emailVerified and kc_user.email,
            "last_sync": datetime.utcnow(),
        }

        required_actions = []
        if hasattr(kc_user, "requiredActions"):
            required_actions = kc_user.requiredActions

        sync_payload = datadef.SyncUserPayload(
            force=force_sync,
            sync_actions=sync_actions,
            user_data=user_data,
            required_actions=required_actions,
        )

        synced_user = await agg.sync_user(sync_payload)
        return synced_user, None


class SendAction(Command):
    """
    Send required actions to user in Keycloak (e.g., UPDATE_PASSWORD, VERIFY_EMAIL).
    Manages user action requirements and integrates with Keycloak's action execution system.
    Updates user's required actions list if marked as required for enforcement.
    """

    class Meta:
        key = "send-action"
        resources = ("user",)
        tags = ["user"]
        auth_required = True
        policy_required = True

    Data = datadef.SendActionPayload

    async def _process(self, agg, stm, payload):
        rootobj = agg.get_rootobj()
        user_id = rootobj._id

        await kc_admin.execute_actions(
            user_id=user_id, actions=payload.actions, redirect_uri=config.REDIRECT_URL
        )
        await agg.track_user_action(payload)

        if payload.required:
            kc_user = await kc_admin.get_user(user_id)
            required_action = kc_user.requiredActions
            actions = [
                action for action in payload.actions if action not in required_action
            ]
            required_action.extend(actions)
            await kc_admin.update_user(
                user_id=user_id, payload={"requiredActions": required_action}
            )


class SendVerification(Command):
    """
    Send email verification request to user through Keycloak.
    Updates user record with verification request timestamp for tracking.
    """

    class Meta:
        key = "send-verification"
        resources = ("user",)
        tags = ["user"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        rootobj = agg.get_rootobj()
        await kc_admin.send_verify_email(rootobj._id)
        await agg.update_user(dict(last_verified_request=datetime.utcnow()))


class DeactivateUser(Command):
    """
    Deactivate user account in both local system and Keycloak.
    Disables user login while preserving account data for potential reactivation.
    """

    class Meta:
        key = "deactivate-user"
        resources = ("user",)
        tags = ["user"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        rootobj = agg.get_rootobj()
        # Get full user representation from Keycloak
        kc_user = await kc_admin.get_user(rootobj._id)
        if not kc_user:
            raise ValueError(f"User {rootobj._id} not found in Keycloak")

        # Update enabled status and send back full representation
        user_data = {
            "email": kc_user.email,
            "username": kc_user.username,
            "firstName": kc_user.firstName,
            "lastName": kc_user.lastName,
            "enabled": False,
            "emailVerified": kc_user.emailVerified,
        }
        if hasattr(kc_user, "requiredActions"):
            user_data["requiredActions"] = kc_user.requiredActions

        await kc_admin.update_user(rootobj._id, user_data)
        await agg.deactivate_user()


class ActivateUser(Command):
    """
    Reactivate previously deactivated user account.
    Enables user login in both Keycloak and local system state.
    """

    class Meta:
        key = "activate-user"
        resources = ("user",)
        tags = ["user"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        rootobj = agg.get_rootobj()
        # Get full user representation from Keycloak
        kc_user = await kc_admin.get_user(rootobj._id)
        if not kc_user:
            raise ValueError(f"User {rootobj._id} not found in Keycloak")

        # Update enabled status and send back full representation
        user_data = {
            "email": kc_user.email,
            "username": kc_user.username,
            "firstName": kc_user.firstName,
            "lastName": kc_user.lastName,
            "enabled": True,
            "emailVerified": kc_user.emailVerified,
        }
        if hasattr(kc_user, "requiredActions"):
            user_data["requiredActions"] = kc_user.requiredActions
        await kc_admin.update_user(rootobj._id, user_data)
        await agg.activate_user()


class SendUserAction(Command):
    """
    Send a user action to the user email (e.g. password change).
    """

    class Meta:
        key = "send-user-action"
        resources = ("user",)
        tags = ["user"]
        auth_required = True
        description = "Send a user action to the user email"

    Data = datadef.ChangeActionPayload

    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        notify_service = getattr(context.service_proxy, config.SERVICE_CLIENT, None)

        if not notify_service:
            raise RuntimeError("Notification service client is not found")


        window_minutes = userconf.RATE_LIMIT_WINDOW_MINUTES
        max_requests = userconf.MAX_REQUESTS_PER_WINDOW
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)

        user = agg.get_rootobj()
        if not user:
            raise ValueError("No user aggregate found")

        recipient_email = user.verified_email or user.telecom__email
        if not recipient_email:
            raise ValueError("User does not have an email address associated with their account to receive action instructions.")

        all_recent_actions = await stm.find_all(
            "user_action",
            where=dict(
                user_id=user._id,
                name=f"{payload.action_type.lower().replace('_', '-')}-action",
                **{"_created.gt": window_start}
            )
        )

        if len(all_recent_actions) >= max_requests:
            raise ValueError(f"Too many action requests. Please wait {window_minutes} minutes.")

        if any(getattr(a.status, "value", a.status) == "PENDING" for a in all_recent_actions):
            raise ValueError("A user action request is already pending. Please complete or cancel it before requesting a new one.")


        # Record the action to get its ID before sending
        action_data = serialize_mapping(payload)
        action_data["user_id"] = user._id
        result = await agg.record_user_action(action_data)


        list_profile = await stm.find_all(
            "profile",
            where=dict(user_id=user._id, status='ACTIVE', current_profile=True)
        )

        if not list_profile:
             raise ValueError("No active profile found for this user to determine target application")

        realm_accesses = set([profile.realm for profile in list_profile])
        target_realm = next(iter(realm_accesses), None)
        base_url = userconf.REALM_URL_MAPPER.get(target_realm, "/") if target_realm else "/"

        if payload.action_type == "PASSWORD_CHANGE":
            change_password_route = getattr(userconf, "CHANGE_PASSWORD_PATH", "/change-password")
            action_link = f"{base_url.rstrip('/')}{change_password_route}?action_id={result.get('action_id')}"
            template_key = "password-change-action"
        else:
            raise ValueError(f"Unsupported action type {payload.action_type}")

        await notify_service.send(
            "rfx-notify:send-notification",
            command="send-notification",
            resource="notification",
            payload={
                "channel": "EMAIL",
                "recipients": [recipient_email],
                "template_key": template_key,
                "content_type": "HTML",
                "template_data": {
                    "action_link": action_link,
                    "user_name": user.name__given or user.username or "User",
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
                "source": "rfx-idm",
            },
        )

        yield agg.create_response(serialize_mapping(result), _type="idm-response")


# ============ Organization Context =============


class CreateOrganization(Command):
    """
    Create new organization with creator as initial admin profile.
    Automatically generates profile for organization creator with full permissions
    and sets up organizational context for multi-tenant operations.
    """

    Data = datadef.CreateOrganizationPayload

    class Meta:
        key = "create-organization"
        resource_init = True
        resources = ("organization",)
        tags = ["organization", "create"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        profile_id = UUID_GENR()
        org_data = serialize_mapping(payload)
        org = await agg.create_organization(org_data)

        yield agg.create_response(serialize_mapping(org), _type="idm-response")


class UpdateOrganization(Command):
    """
    Update organization metadata and settings.
    Modifies organizational attributes while preserving structural integrity.
    """

    class Meta:
        key = "update-organization"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True
        policy_required = True

    Data = datadef.UpdateOrganizationPayload

    async def _process(self, agg, stm, payload):
        result = await agg.update_organization(serialize_mapping(payload))
        yield agg.create_response(serialize_mapping(result), _type="idm-response")


class ActivateOrganization(Command):
    """
    Reactivate previously deactivated organization.
    Restores organizational operations and access for all associated profiles.
    """

    class Meta:
        key = "activate-organization"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.activate_organization()
        yield agg.create_response(serialize_mapping(result), _type="idm-response")


class DeactivateOrganization(Command):
    """
    Deactivate organization and cascade to all profiles.
    Suspends organizational operations while maintaining data for audit.
    """

    class Meta:
        key = "deactivate-organization"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.deactivate_organization()
        yield agg.create_response(serialize_mapping(result), _type="idm-response")


class CreateOrgRole(Command):
    """
    Create custom role within organization scope.
    Defines organization-specific permissions and access controls.
    """

    class Meta:
        key = "create-org-role"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True
        policy_required = True

    Data = datadef.CreateOrgRolePayload

    async def _process(self, agg, stm, payload):
        result = await agg.create_org_role(serialize_mapping(payload))
        yield agg.create_response(serialize_mapping(result), _type="idm-response")


class UpdateOrgRole(Command):
    """
    Update organization role permissions and metadata.
    Modifies role definition while preserving existing assignments.
    """

    class Meta:
        key = "update-org-role"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True
        policy_required = True

    Data = datadef.UpdateOrgRolePayload

    async def _process(self, agg, stm, payload):
        result = await agg.update_org_role(serialize_mapping(payload))
        yield agg.create_response(serialize_mapping(result), _type="idm-response")


class RemoveOrgRole(Command):
    """
    Remove organization role and revoke from all profiles.
    Deletes role definition and cascades to remove all assignments.
    """

    class Meta:
        key = "remove-org-role"
        resources = ("organization",)
        tags = ["organization"]
        auth_required = True
        policy_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_org_role()
        yield agg.create_response({"status": "success"}, _type="idm-response")


# ============ Invitation Context =============


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
        yield agg.create_response(result, _type="idm-response")


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
        yield agg.create_response(result, _type="idm-response")


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
        yield agg.create_response(result, _type="idm-response")


# ============ Profile Context =============


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
        role_keys = data.pop("role_keys", ["VIEWER"])
        profile = await agg.create_profile(data)

        await agg.update_profile_roles({
            "profile_id": profile._id,
            "role_keys": role_keys
        })

        yield agg.create_response(serialize_mapping(profile), _type="idm-response")


class CreateProfileInOrg(Command):
    """
    Create user profile directly within specified organization.
    Bypasses invitation process for streamlined profile creation.
    """

    class Meta:
        key = "create-profile-in-org"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        resource_init = True
        policy_required = True

    Data = datadef.CreateProfileInOrgPayload

    async def _process(self, agg, stm, payload):
        profile_data = serialize_mapping(payload)
        role_keys = profile_data.pop("role_keys", ["VIEWER"])

        # Pre-validate OWNER role before creating profile to avoid orphaned records
        if "OWNER" in role_keys:
            organization_id = profile_data.get("organization_id")

            # Find all existing OWNER roles
            existing_owner_roles = await stm.find_all(
                "profile_role",
                where=dict(role_key="OWNER")
            )

            # Check if any OWNER exists in the target organization
            for owner_role in existing_owner_roles:
                owner_profile = await stm.fetch("profile", owner_role.profile_id)
                if (owner_profile and
                    owner_profile.organization_id == organization_id and
                    owner_profile.status == "ACTIVE"):
                    raise ValueError(f"Organization can have only one OWNER role assigned. Current owner: {owner_profile.name__family} {owner_profile.name__given}")

        # Create the profile
        result = await agg.create_profile_in_org(profile_data)

        # Assign roles - if this fails, the transaction will rollback the profile creation
        try:
            await agg.update_profile_roles({
                "profile_id": result.get("profile_id"),
                "role_keys": role_keys
            })
        except Exception as e:
            # Re-raise to trigger transaction rollback
            raise ValueError(f"Failed to assign roles to profile: {str(e)}")

        yield agg.create_response(serialize_mapping(result), _type="idm-response")


# class SwitchProfile(Command):
#     """
#     Switch active organization for user profile.
#     Updates current profile's organization context for multi-tenant operations.
#     """

#     class Meta:
#         key = "switch-profile"
#         resources = ("profile",)
#         tags = ["profile", "switch"]
#         auth_required = True
#         policy_required = True

#     async def _process(self, agg, stm, payload):
#         await agg.switch_profile()


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
        payload = serialize_mapping(payload)
        role_keys = payload.pop("role_keys", None)

        # Pre-validate OWNER role if being added
        if role_keys is not None and "OWNER" in role_keys:
            profile = agg.get_rootobj()

            # Check if profile already has OWNER role
            existing_roles = await stm.find_all('profile_role', where=dict(
                profile_id=profile._id,
            ))
            existing_keys = {r.role_key for r in existing_roles}

            # Only validate if OWNER is being newly added (not already assigned)
            if "OWNER" not in existing_keys:
                # Find all existing OWNER roles in the organization
                all_owner_roles = await stm.find_all(
                    "profile_role",
                    where=dict(role_key="OWNER")
                )

                for owner_role in all_owner_roles:
                    if owner_role.profile_id != profile._id:
                        owner_profile = await stm.fetch("profile", owner_role.profile_id)
                        if (owner_profile and
                            owner_profile.organization_id == profile.organization_id and
                            owner_profile.status == "ACTIVE"):
                            raise ValueError(f"Organization can have only one OWNER role assigned. Current owner: {owner_profile.name__family} {owner_profile.name__given}")

        await agg.update_profile(payload)

        if role_keys is not None:
            try:
                await agg.update_profile_roles({
                    "profile_id": str(agg.get_rootobj()._id),
                    "role_keys": role_keys
                })
            except Exception as e:
                # Re-raise to trigger transaction rollback
                raise ValueError(f"Failed to update profile roles: {str(e)}")


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


# # ============ Profile Role Management =============


# class AssignRoleToProfile(Command):
#     """
#     Assign system or organization role to profile.
#     Grants specific permissions within organizational context.
#     """

#     class Meta:
#         key = "assign-role-to-profile"
#         resources = ("profile",)
#         tags = ["profile"]
#         auth_required = True
#         policy_required = True

#     Data = datadef.AssignRolePayload

#     async def _process(self, agg, stm, payload):
#         role = await agg.assign_role_to_profile(serialize_mapping(payload))
#         agg.create_response(role, _type="idm-response")


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


class AddGroupToProfile(Command):
    """
    Add profile to security group.
    Associates profile with group for permissions and organization structure.
    """

    class Meta:
        key = "add-group-to-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        internal = True

    Data = datadef.AddGroupToProfilePayload

    async def _process(self, agg, stm, payload):
        await agg.add_group_to_profile(payload)


class RemoveGroupFromProfile(Command):
    """
    Remove profile from security group.
    Removes group association while preserving other group memberships.
    """

    class Meta:
        key = "remove-group-from-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        internal = True

    Data = datadef.RemoveGroupFromProfilePayload

    async def _process(self, agg, stm, payload):
        await agg.remove_group_from_profile(payload)


# ============ Group Management =============


class AssignGroupToProfile(Command):
    """
    Assign security group to profile with permissions validation.
    Creates group membership within organizational security model.
    """

    class Meta:
        key = "assign-group-to-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        internal = True

    Data = datadef.AddGroupToProfilePayload

    async def _process(self, agg, stm, payload):
        group = await agg.assign_group_to_profile(payload)
        yield agg.create_response(serialize_mapping(group), _type="idm-response")


class RevokeGroupFromProfile(Command):
    """
    Revoke group membership from profile.
    Removes specific group association while maintaining other memberships.
    """

    class Meta:
        key = "revoke-group-from-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        internal = True

    Data = datadef.RemoveGroupFromProfilePayload

    async def _process(self, agg, stm, payload):
        await agg.revoke_group_from_profile(payload)
        yield agg.create_response({"status": "success"}, _type="idm-response")


class ClearAllGroupFromProfile(Command):
    """
    Remove all group memberships from profile.
    Clears all group associations while preserving profile structure.
    """

    class Meta:
        key = "clear-group-from-profile"
        resources = ("profile",)
        tags = ["profile"]
        auth_required = True
        internal = True

    async def _process(self, agg, stm, payload):
        await agg.clear_all_group_from_profile()
        yield agg.create_response({"status": "success"}, _type="idm-response")


class CreateGroup(Command):
    """
    Create new security group with organizational scope.
    Establishes group structure for permissions and access management.
    """

    class Meta:
        key = "create-group"
        resource_init = True
        resources = ("group",)
        tags = ["group"]
        auth_required = True
        description = "Create a new group"
        internal = True

    Data = datadef.CreateGroupPayload

    async def _process(self, agg, stm, payload):
        group = await agg.create_group(payload)
        yield agg.create_response(serialize_mapping(group), _type="idm-response")


class UpdateGroup(Command):
    """
    Update security group metadata and permissions.
    Modifies group definition while maintaining existing memberships.
    """

    class Meta:
        key = "update-group"
        resources = ("group",)
        tags = ["group"]
        auth_required = True
        description = "Update an existing group"
        internal = True

    Data = datadef.UpdateGroupPayload

    async def _process(self, agg, stm, payload):
        group = await agg.update_group(payload)
        yield agg.create_response(serialize_mapping(group), _type="idm-response")


class DeleteGroup(Command):
    """
    Soft delete security group and remove all profile associations.
    Deactivates group while preserving audit trail and historical memberships.
    """

    class Meta:
        key = "delete-group"
        resources = ("group",)
        tags = ["group"]
        auth_required = True
        description = "Delete (soft) a group and remove all profile associations"
        internal = True

    async def _process(self, agg, stm, payload):
        await agg.delete_group()
        yield agg.create_response({"status": "success"}, _type="idm-response")

