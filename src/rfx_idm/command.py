from datetime import timedelta
from fluvius.helper import timestamp
from fluvius.data import serialize_mapping, UUID_GENR
from fluvius.data.exceptions import ItemNotFoundError
from fluvius.error import BadRequestError

from .domain import IDMDomain
from .integration import kc_admin
from . import datadef, config, logger
from rfx_user import config as userconf

processor = IDMDomain.command_processor
Command = IDMDomain.Command


# ============ Mixins =============


class SyncUserMixin:
    """Provides reusable logic for synchronizing user data from Keycloak."""

    async def _sync_from_keycloak(
        self, agg, force_sync: bool = False, sync_actions: bool = True
    ):
        """Pull latest user info from Keycloak and update local state."""
        user = agg.get_rootobj()
        user_id = user._id
        try:
            kc_user = await kc_admin.get_user(user_id)
        except BadRequestError as e:
            if "User not found" in str(e):
                return None, {"status": "skipped", "reason": "User not found in Keycloak"}
            raise

        if not kc_user:
            return None, {"status": "skipped", "reason": "User not found in Keycloak"}

        user_data = {
            "name__family": kc_user.lastName,
            "name__given": kc_user.firstName,
            "telecom__email": kc_user.email,
            "username": kc_user.username,
            "active": kc_user.enabled,
            "verified_email": kc_user.email if kc_user.emailVerified else None,
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
        return synced_user, {"status": "success", "user_id": str(user_id)}


class UserProvisionMixin:
    """Provides reusable logic for provisioning users in Keycloak and local system."""

    async def _find_kc_user_by_identifiers(self, email=None):
        """Exact-match lookup in Keycloak by username then email."""
        kc_user = None

        if email:
            candidates = await kc_admin.find_user(email)
            for u in candidates:
                if u.email == email:
                    kc_user = u
                    break
        return kc_user

    async def _trigger_kc_onboarding(self, user_id, realm=None):
        """Trigger Keycloak required-action onboarding emails."""
        realm = realm or config.REALM
        # Use realm URL mapper if available, otherwise fallback to root
        redirect_url = config.REALM_URL_MAPPER.get(realm, "/") if hasattr(config, "REALM_URL_MAPPER") else "/"
        try:
            await kc_admin.execute_actions(
                user_id=user_id,
                actions=["UPDATE_PASSWORD", "VERIFY_EMAIL"],
                redirect_uri=redirect_url,
            )
        except Exception as e:
            logger.warning(f"Failed to execute Keycloak actions for user {user_id}: {e}")

    async def _ensure_local_user(
        self, stm, agg, kc_user, is_superuser=False, required_actions=None, **extra_data
    ):
        """Standardized local user synchronization and upsert logic."""
        import copy
        try:
            return await stm.fetch("user", kc_user.id)
        except Exception:
            pass

        realm_access = copy.deepcopy(DEFAULT_REALM_ACCESS)
        if config.ALLOW_CREATE_SYS_ADMIN:
            if is_superuser and "sys_admin" not in realm_access["roles"]:
                realm_access["roles"].append("sys_admin")
        resource_access = copy.deepcopy(DEFAULT_RESOURCE_ACCESS)

        # Build standard user data mapping
        user_data = {
            "_id": kc_user.id,
            "username": getattr(kc_user, "username", None) or extra_data.get("username"),
            "active": getattr(kc_user, "enabled", True),
            "is_super_admin": is_superuser,
            "telecom__email": getattr(kc_user, "email", None) or extra_data.get("telecom__email"),
            "realm_access": realm_access,
            "resource_access": resource_access,
        }

        # Merge names and telecom info from Keycloak if available, or fall back to extra_data
        user_data.update({
            "name__given": getattr(kc_user, "firstName", None) or extra_data.get("name__given"),
            "name__family": getattr(kc_user, "lastName", None) or extra_data.get("name__family"),
            "name__middle": extra_data.get("name__middle"),
            "name__prefix": extra_data.get("name__prefix"),
            "name__suffix": extra_data.get("name__suffix"),
            "telecom__phone": extra_data.get("telecom__phone"),
        })

        # Multi-field verification data
        user_data.update({
            "verified_email": extra_data.get("verified_email")
            or (
                getattr(kc_user, "email", None)
                if getattr(kc_user, "emailVerified", False)
                else None
            ),
            "verified_phone": extra_data.get("verified_phone"),
        })

        user = await agg.create_user(user_data)

        # Record initial required actions in local DB if reference table allows
        if required_actions:
            for action_key in required_actions:
                try:
                    # Ensure action exists in ref__action
                    await stm.find_one("ref__action", where=dict(key=action_key))
                except ItemNotFoundError:
                    logger.warning(
                        f"Required action '{action_key}' for user {kc_user.id} not found in ref__action."
                    )

        # Sync sys_admin role to Keycloak if needed
        if config.ALLOW_CREATE_SYS_ADMIN and is_superuser:
            try:
                await kc_admin.add_user_roles(kc_user.id, ["sys_admin"])
            except Exception as e:
                logger.warning(
                    f"Failed to assign sys_admin role in Keycloak for {kc_user.id}: {e}"
                )

        return user


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


class CreateUser(Command, UserProvisionMixin):
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

        # Prepare Keycloak user data.
        kc_user_data = {
            "email": payload.email,
            "username": payload.username,
            "firstName": payload.first_name or "",
            "lastName": payload.last_name or "",
            "enabled": payload.is_active,
            "emailVerified": email_verified,
            "requiredActions": ["UPDATE_PASSWORD", "VERIFY_EMAIL"],
        }

        # Create user in Keycloak
        kc_user = await self._find_kc_user_by_identifiers(
            email=payload.email
        )
        user_already_in_kc = False

        if not kc_user:
            try:
                kc_user = await kc_admin.create_user(kc_user_data)
            except BadRequestError as e:
                if any(term in str(e).lower() for term in ["conflict", "exists", "already"]):
                    kc_user = await self._find_kc_user_by_identifiers(
                        email=payload.email
                    )
                    if not kc_user:
                        raise e
                    user_already_in_kc = True
                else:
                    raise
        else:
            user_already_in_kc = True

        if user_already_in_kc:
            # Check if local record exists
            try:
                await stm.find_one("user", where=dict(_id=kc_user.id))
                # If we reach here, user exists both in KC and locally.
                raise BadRequestError(
                    "A00.400",
                    f"User with identifier {payload.username or payload.email} already exists."
                )
            except ItemNotFoundError:
                # User exists in KC but NOT locally. This is fine, proceed to sync.
                pass

        # Ensure local record is synced
        user = await self._ensure_local_user(
            stm,
            agg,
            kc_user,
            is_superuser=payload.is_superuser,
            username=payload.username,
            telecom__email=payload.email,
            name__given=payload.first_name,
            name__family=payload.last_name,
            name__middle=payload.middle_name,
            name__prefix=payload.name_prefix,
            name__suffix=payload.name_suffix,
            telecom__phone=payload.phone,
            verified_email=(
                payload.verified_email or (payload.email if email_verified else None)
            ),
            verified_phone=payload.verified_phone,
            required_actions=getattr(kc_user, "requiredActions", None),
        )

        # Trigger onboarding emails
        await self._trigger_kc_onboarding(kc_user.id, realm=None)

        yield agg.create_response(serialize_mapping(user), _type="idm-response")


class UpdateUser(Command, SyncUserMixin):
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
        # Handle realm_access based on is_superuser
        if payload.is_superuser is not None:
            if getattr(config, "ALLOW_CREATE_SYS_ADMIN", False):
                import copy
                realm_access = copy.deepcopy(rootobj.realm_access) if rootobj.realm_access else copy.deepcopy(DEFAULT_REALM_ACCESS)
                roles = realm_access.get("roles", [])
                if payload.is_superuser and "sys_admin" not in roles:
                    roles.append("sys_admin")
                elif not payload.is_superuser and "sys_admin" in roles:
                    roles.remove("sys_admin")
                realm_access["roles"] = roles
                user_updates["realm_access"] = realm_access
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

        if payload.is_superuser is not None and getattr(config, "ALLOW_CREATE_SYS_ADMIN", False):
            try:
                if payload.is_superuser:
                    await kc_admin.add_user_roles(user_id, ["sys_admin"])
                else:
                    await kc_admin.delete_user_roles(user_id, ["sys_admin"])
            except Exception as e:
                logger.warning(f"Failed to update sys_admin role in Keycloak for {user_id}: {e}")

        update_performed = (
            bool(kc_payload) or bool(payload.password) or bool(user_updates)
        )

        # Trigger sync from Keycloak if requested or after an update to ensure consistency
        # Force sync if update was performed to ensure local DB reflects Keycloak state
        sync_requested = payload.sync_remote or payload.force_sync or update_performed
        force_requested = payload.force_sync or update_performed
        sync_only = sync_requested and not update_performed

        synced_user = None
        sync_status = None
        if sync_requested:
            synced_user, sync_status = await self._sync_from_keycloak(
                agg, force_sync=force_requested, sync_actions=payload.sync_actions
            )

            if sync_status and sync_only:
                yield agg.create_response(sync_status, _type="idm-response")
                return

        result_user = synced_user or updated_user
        response_payload = serialize_mapping(result_user)

        if sync_status and not sync_only:
            response_payload["sync_status"] = sync_status

        yield agg.create_response(response_payload, _type="idm-response")


class SyncUser(Command, SyncUserMixin):
    """
    Manually trigger synchronization of user attributes from Keycloak.
    Ensures local datastore is consistent with identity provider state.
    """

    class Meta:
        key = "sync-user"
        resources = ("user",)
        tags = ["user", "sync"]
        auth_required = True
        policy_required = True

    Data = datadef.SyncUserRequestPayload

    async def _process(self, agg, stm, payload):
        # Check if sync is needed
        if not payload.force:
            user = agg.get_rootobj()
            if getattr(user, "last_sync", None):
                # Don't sync if last sync was less than 5 minutes ago
                if (timestamp().replace(tzinfo=None) - user.last_sync).total_seconds() < 300:
                    yield agg.create_response(
                        {"status": "skipped", "reason": "Recently synced"},
                        _type="idm-response",
                    )
                    return

        synced_user, sync_status = await self._sync_from_keycloak(
            agg, force_sync=payload.force, sync_actions=payload.sync_actions
        )

        if synced_user:
            yield agg.create_response(
                serialize_mapping(synced_user), _type="idm-response"
            )
        else:
            yield agg.create_response(sync_status, _type="idm-response")


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
        await agg.update_user(dict(last_verified_request=timestamp().replace(tzinfo=None)))


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


class SendUserAction(Command, UserProvisionMixin):
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
        window_minutes = userconf.RATE_LIMIT_WINDOW_MINUTES
        max_requests = userconf.MAX_REQUESTS_PER_WINDOW
        window_start = timestamp().replace(tzinfo=None) - timedelta(minutes=window_minutes)

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
                action_type=payload.action_type,
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

        try:
            list_profile = await stm.find_all(
                "profile",
                where=dict(user_id=user._id, status='ACTIVE')
            )
        except ItemNotFoundError as e:
            list_profile = None

        if list_profile:
            realm_accesses = {p.realm for p in list_profile if p.realm}
        else:
            r = getattr(config, "REALM", None)
            realm_accesses = {r} if r else set()

        target_realm = next(iter(realm_accesses), None)
        mapper = getattr(config, "REALM_URL_MAPPER", None) or {}
        default_realm = getattr(config, "REALM", None)
        redirect_url = (
            mapper.get(target_realm)
            or (mapper.get(default_realm) if default_realm else None)
            or config.DEFAULT_SIGNIN_REDIRECT_URI
        )

        allowed_actions = ["UPDATE_PASSWORD", "VERIFY_EMAIL"]
        if payload.action_type not in allowed_actions:
            raise ValueError(f"Unsupported action type {payload.action_type}")

        kc_actions = [payload.action_type]

        await kc_admin.execute_actions(
            user_id=user._id,
            actions=kc_actions,
            redirect_uri=redirect_url,
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

        # Validate target realm against OPERATION_VALID_REALMS
        # from . import config
        if config.OPERATION_VALID_REALMS is not None:
            target_realm = data.get("realm")
            if target_realm not in config.OPERATION_VALID_REALMS:
                raise ValueError(f"Realm '{target_realm}' is not valid for profile creation.")

        role_keys = data.pop("role_keys", ["VIEWER"])
        profile = await agg.create_profile(data)

        profile_id = profile._id if hasattr(profile, '_id') else profile.get("_id")

        await agg.update_profile_roles({
            "profile_id": profile_id,
            "role_keys": role_keys
        })

        # Send welcome email
        if data.get("realm"):
            context = agg.get_context()
            notify_service = getattr(context.service_proxy, config.NOTIFY_CLIENT, None)

            if notify_service:
                target_realm = data.get("realm")
                base_url = userconf.REALM_URL_MAPPER.get(target_realm, "/") if target_realm and userconf.REALM_URL_MAPPER else "/"
                action_link = base_url

                # Extract company name from realm (e.g. "triptech" from "app.triptech.vn")
                realm_parts = target_realm.split('.') if target_realm else []
                company_name = realm_parts[1].capitalize() if len(realm_parts) > 1 else (target_realm or "Our Company")

                try:
                    await notify_service.send(
                        f"{config.NOTIFY_NAMESPACE}:send-notification",
                        command="send-notification",
                        resource="notification",
                        payload={
                            "channel": "EMAIL",
                            "recipients": [data.get("telecom__email")],
                            "template_key": "create-user-email",
                            "content_type": "HTML",
                            "template_data": {
                                "user_name": f"{data.get('name__given') or ''} {data.get('name__family') or ''}".strip() or data.get('username') or "User",
                                "username": data.get("username") or data.get("telecom__email"),
                                "action_link": action_link,
                                "company": company_name,
                            },
                        },
                        identifier=UUID_GENR(),
                        _headers={},
                        _context={
                            "audit": {
                                "user_id": str(context.user_id) if context.user_id else None,
                                "profile_id": str(context.profile_id) if context.profile_id else None,
                                "organization_id": str(context.organization_id) if context.organization_id else None,
                                "realm": context.realm,
                            },
                            "source": "rfx-idm",
                        },
                    )
                except Exception as e:
                    logger.warning(f"Failed to send welcome email for profile {profile_id}: {e}")

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

        # Validate target realm against OPERATION_VALID_REALMS
        if config.OPERATION_VALID_REALMS is not None:
            target_realm = profile_data.get("realm")
            if target_realm not in config.OPERATION_VALID_REALMS:
                raise ValueError(f"Realm '{target_realm}' is not valid for profile creation.")

        role_keys = profile_data.pop("role_keys", ["VIEWER"])

        # Early check for organization authorization to prevent information leakage
        intended_organization_id = str(profile_data.get("organization_id"))
        context = agg.get_context()
        current_org_id = str(context.organization_id)
        if intended_organization_id != current_org_id:
            curr_user = await stm.fetch("user", context.user_id)
            roles = curr_user.realm_access.get("roles", []) if curr_user.realm_access else []
            is_admin = "sys_admin" in roles

            # Allow bypass if user is in the system organization
            is_system_org = config.SYSTEM_ORGANIZATION_ID is not None and current_org_id == str(config.SYSTEM_ORGANIZATION_ID)

            if not is_system_org and not is_admin:
                raise ValueError("You are not a member of that organization")

        # Pre-validate OWNER role before creating profile to avoid orphaned records
        if "OWNER" in role_keys:
            organization_id = profile_data.get("organization_id")

            all_profile_in_orgs = await stm.find_all('profile', where=dict(
                organization_id=organization_id,
                status="ACTIVE"
            ))

            for p in all_profile_in_orgs:
                try:
                    profile_role = await stm.find_one('profile_role', where=dict(
                        profile_id=p._id,
                        role_key='OWNER'
                    ))
                    # If.find_one succeeds, an OWNER role exists
                    raise ValueError(f"Organization already has an owner: {p.name__family} {p.name__given}")
                except ItemNotFoundError:
                    pass

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


class CreateProfileUserInOrg(Command, UserProvisionMixin):
    """
    Create a profile within an organization for a user, optionally creating the
    Keycloak user on the fly.

    Behaviour is controlled by ``assign_to_existed_user``:

    - ``True``  → look up the user by username/email in Keycloak; raise if not found.
    - ``False`` → Intent is to create a NEW user. If the user already exists in Keycloak,
                  raises an error. If NOT found, creates the user with required actions
                  (UPDATE_PASSWORD + VERIFY_EMAIL).

    In both cases a local ``user`` record is synchronized/created, then a profile
    is created in the target organization.
    """

    class Meta:
        key = "create-profile-user-in-org"
        resources = ("profile",)
        tags = ["profile", "user"]
        auth_required = True
        resource_init = True
        policy_required = True

    Data = datadef.CreateProfileUserInOrgPayload

    # ------------------------------------------------------------------
    # Main process
    # ------------------------------------------------------------------

    async def _process(self, agg, stm, payload):
        profile_data = serialize_mapping(payload)

        # Strip user-resolution-only fields before building the profile record
        assign_to_existed_user = profile_data.pop("assign_to_existed_user", False)
        is_active = profile_data.pop("is_active", True)
        is_superuser = profile_data.pop("is_superuser", False)

        # Validate realm
        target_realm = profile_data.get("realm")
        if config.OPERATION_VALID_REALMS is not None:
            if target_realm not in config.OPERATION_VALID_REALMS:
                raise ValueError(f"Realm '{target_realm}' is not valid for profile creation.")

        role_keys = profile_data.pop("role_keys", ["VIEWER"])

        # Validate org authorization (mirrors CreateProfileInOrg)
        intended_organization_id = str(profile_data.get("organization_id"))
        context = agg.get_context()
        current_org_id = str(context.organization_id)
        if intended_organization_id != current_org_id:
            curr_user = await stm.fetch("user", context.user_id)
            roles = curr_user.realm_access.get("roles", []) if curr_user.realm_access else []
            is_admin = "sys_admin" in roles
            is_system_org = (
                config.SYSTEM_ORGANIZATION_ID is not None
                and current_org_id == str(config.SYSTEM_ORGANIZATION_ID)
            )
            if not is_system_org and not is_admin:
                raise ValueError("You are not a member of that organization")

        # Pre-validate OWNER uniqueness (mirrors CreateProfileInOrg)
        if "OWNER" in role_keys:
            organization_id = profile_data.get("organization_id")
            all_profile_in_orgs = await stm.find_all(
                "profile", where=dict(organization_id=organization_id, status="ACTIVE")
            )
            for p in all_profile_in_orgs:
                try:
                    await stm.find_one(
                        "profile_role", where=dict(profile_id=p._id, role_key="OWNER")
                    )
                    raise ValueError(
                        f"Organization already has an owner: {p.name__family} {p.name__given}"
                    )
                except ItemNotFoundError:
                    pass

        # Resolve the Keycloak user
        kc_user = await self._find_kc_user_by_identifiers(
            email=payload.telecom__email
        )
        user_was_created = False

        if kc_user and not assign_to_existed_user:
            try:
                await stm.find_one("user", where=dict(_id=kc_user.id))
                lookup_key = payload.username or payload.telecom__email
                raise ValueError(
                    f"User with identifier '{lookup_key}' already exists. "
                    "Check the box to create a new profile to the user."
                )
            except ItemNotFoundError:
                pass

        if not kc_user:
            if assign_to_existed_user:
                lookup_key = payload.username or payload.telecom__email
                raise ValueError(
                    f"User not found for identifier '{lookup_key}'. "
                    "Uncheck the box to create a new user."
                )

            # Create new user in Keycloak
            kc_user_data = {
                "email": payload.telecom__email,
                "username": payload.username or payload.telecom__email,
                "firstName": payload.name__given or "",
                "lastName": payload.name__family or "",
                "enabled": is_active,
                "emailVerified": False,
                "requiredActions": ["UPDATE_PASSWORD", "VERIFY_EMAIL"],
            }
            try:
                kc_user = await kc_admin.create_user(kc_user_data)
                user_was_created = True
            except BadRequestError as e:
                if any(term in str(e).lower() for term in ["conflict", "exists", "already"]):
                    kc_user = await self._find_kc_user_by_identifiers(
                        email=payload.telecom__email
                    )
                    if not kc_user:
                        raise e
                    user_was_created = False
                else:
                    raise

            # Trigger onboarding emails
            await self._trigger_kc_onboarding(kc_user.id, target_realm)

        # Check for existing profile in this organization's realm
        if not user_was_created:
            try:
                existing_profile = await stm.find_one(
                    "profile",
                    where=dict(
                        user_id=kc_user.id,
                        organization_id=intended_organization_id,
                        realm=target_realm,
                    ),
                )
            except ItemNotFoundError:
                existing_profile = None
            if existing_profile:
                status_msg = "ACTIVE" if existing_profile.status == 'ACTIVE' else "waiting for verification"
                raise ValueError(f"User already has a profile in this organization (status: {status_msg}).")

        # Ensure local record is synced
        await self._ensure_local_user(
            stm,
            agg,
            kc_user,
            is_superuser=is_superuser,
            username=payload.username or payload.telecom__email,
            telecom__email=payload.telecom__email,
            name__given=payload.name__given,
            name__family=payload.name__family,
            telecom__phone=payload.telecom__phone,
            required_actions=getattr(kc_user, "requiredActions", None),
        )

        # Inject resolved user_id; username belongs on user, not profile
        profile_data["user_id"] = kc_user.id
        profile_data.pop("username", None)

        if user_was_created:
            # Brand-new user: create an ACTIVE profile and assign roles immediately.
            profile_data["status"] = "ACTIVE"
            result = await agg.create_profile_in_org(profile_data)

            try:
                await agg.update_profile_roles({
                    "profile_id": result.get("profile_id"),
                    "role_keys": role_keys,
                })
            except Exception as e:
                raise ValueError(f"Failed to assign roles to profile: {str(e)}")
        else:
            # Existing user: create an INACTIVE placeholder profile, then send an invitation.
            profile_data["status"] = "INACTIVE"
            result = await agg.create_profile_in_org(profile_data)
            profile_id = result.get("profile_id")
            try:
                await agg.update_profile_roles({
                    "profile_id": profile_id,
                    "role_keys": role_keys,
                })
            except Exception as e:
                raise ValueError(f"Failed to assign roles to profile: {str(e)}")

            invitation_data = {
                "email": payload.telecom__email,
                "duration": 7,
                "message": "",
                "organization_id": profile_data.get("organization_id"),
                "role_keys": role_keys,
                "user_id": str(kc_user.id),
                "profile_id": str(profile_id),
                "realm": profile_data.get("realm")
            }
            try:
                await agg.send_invitation(invitation_data)
            except Exception as e:
                logger.warning(
                    f"Profile {profile_id} created (INACTIVE) but invitation send failed: {e}"
                )
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
                all_profile_in_orgs = await stm.find_all('profile', where=dict(
                    organization_id=profile.organization_id,
                    status="ACTIVE"
                ))

                for p in all_profile_in_orgs:
                    # Skip the current profile being updated
                    if p._id == profile._id:
                        continue

                    try:
                        profile_role = await stm.find_one('profile_role', where=dict(
                            profile_id=p._id,
                            role_key='OWNER'
                        ))
                        # If find_one succeeds, an OWNER role exists
                        raise ValueError(f"Organization already has an owner: {p.name__family} {p.name__given}")
                    except ItemNotFoundError:
                        pass

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

