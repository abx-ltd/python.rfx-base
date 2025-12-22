"""
RFX IDM Authentication Profile Provider

Integrates with Keycloak for user authentication and profile management.
Handles user data synchronization and authorization context setup.
"""

from fluvius.data import DataAccessManager
from fluvius.auth import AuthorizationContext, SessionOrganization, SessionProfile
from fluvius.fastapi.auth import FluviusAuthProfileProvider, KeycloakTokenPayload
from fluvius.error import UnauthorizedError
from . import config

from rfx_user.model import IDMConnector

class RFXIDMAuthProfileProvider(
    FluviusAuthProfileProvider,
    DataAccessManager
):
    """
    Authentication provider for RFX IDM system.
    Handles Keycloak token validation, user profile management, and authorization context.
    """
    __connector__ = IDMConnector
    __automodel__ = True

    def format_user_data(self, data):
        """Extract and format user data from Keycloak token payload."""
        return dict(
            _id=data.sub,
            name__family=data.family_name,
            name__given=data.given_name,
            realm_access=data.realm_access,
            resource_access=data.resource_access,
            telecom__email=data.email,
            username=data.preferred_username,
            verified_email=data.email if data.email_verified else None,
        )

    def __init__(self, app, active_profile=None):
        """Initialize provider with optional active profile override."""
        super(DataAccessManager, self).__init__(app)
        self._active_profile = active_profile

    async def setup_context(self, auth_user: KeycloakTokenPayload) -> AuthorizationContext:
        """
        Set up authorization context from Keycloak token.
        Handles user sync, profile management, and organization resolution.
        """
        async with self.transaction():
            # ---------- User ----------
            user_id = auth_user.sub
            user_data = self.format_user_data(auth_user)
            await self.upsert_data('user', user_data)
            user = await self.fetch('user', user_id)

            # ---------- Profile ----------
            realm_query = dict(user_id=user_id, current_profile=True, status='ACTIVE', _realm=config.REALM)
            curr_profile = await self.find_one('profile', where=realm_query)

            profile = curr_profile

            if not profile:
                realm_profiles = await self.find_all('profile', where=dict(
                    user_id=user_id,
                    status='ACTIVE',
                    _realm=config.REALM
                ))

                if realm_profiles:
                    profile = realm_profiles[0]
                    await self.update_data('profile', identifier=profile._id, current_profile=True)
                else:
                    raise UnauthorizedError('U100-404', f'Profile not found for realm [{config.REALM}].')

            if self._active_profile:
                act_profile = await self.find_one('profile', identifier=self._active_profile._id)
                if not act_profile:
                    raise UnauthorizedError('U100-401', f'Active profile [{self._active_profile}] not found!')

                if profile and profile._id != act_profile._id:
                    await self.update_data('profile', identifier=profile._id, current_profile=False)
                    await self.update_data('profile', identifier=act_profile._id, current_profile=True)

                profile = act_profile

            organization = await self.fetch('organization', profile.organization_id)

        # ---------- Realm/Roles ----------
        realm_access = getattr(auth_user, "realm_access", None)
        if realm_access and isinstance(realm_access, dict):
            iamroles = tuple(realm_access.get("roles", ()))
        else:
            iamroles = tuple()

        realm = config.REALM

        profile_payload = SessionProfile(
            id=profile._id,
            name=profile.name__given or profile.name__family or (profile.telecom__email or ""),
            family_name=profile.name__family or "",
            given_name=profile.name__given or "",
            email=profile.telecom__email,
            username=user.username or user.telecom__email,
            roles=iamroles,
            org_id=profile.organization_id,
            usr_id=user._id,
        )

        organization_payload = SessionOrganization(
            id=organization._id,
            name=getattr(organization, "name", None) or getattr(organization, "business_name", None) or "Organization"
        )

        return AuthorizationContext(
            realm=realm,
            user=auth_user,
            profile=profile_payload,
            organization=organization_payload,
            iamroles=iamroles,
        )
