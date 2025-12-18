"""
RFX Authentication Profile Provider

Integrates with Keycloak for user authentication and profile management.
Handles user data synchronization and authorization context setup.
"""

from types import SimpleNamespace
from fluvius.data import DataAccessManager, UUID_GENR
from fluvius.auth import AuthorizationContext
from fluvius.fastapi.auth import FluviusAuthProfileProvider, KeycloakTokenPayload
from fluvius.error import UnauthorizedError
from . import config

from .model import IDMConnector

class RFXAuthProfileProvider(
    FluviusAuthProfileProvider,
    DataAccessManager
):
    """
    Authentication provider for RFX User system.
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
            await self.upsert('user', user_data)
            user = await self.fetch('user', user_id)

            # ---------- Profile ----------
            realm_query = dict(user_id=user_id, current_profile=True, status='ACTIVE', _realm=config.REALM)
            curr_profile = await self.exist('profile', where=realm_query)

            if not curr_profile:
                existing_profiles = await self.find_all('profile', where=dict(user_id=user_id, status='ACTIVE'))
                organization = None

                if existing_profiles:
                    owner_profile = None
                    for candidate in existing_profiles:
                        owner_role = await self.exist(
                            'profile_role',
                            where=dict(profile_id=candidate._id, role_key='OWNER')
                        )
                        if owner_role:
                            owner_profile = candidate
                            break

                    if owner_profile:
                        organization = await self.fetch('organization', owner_profile.organization_id)

                if organization is None:
                    org_record = self.create('organization', dict(
                        _id=UUID_GENR(),
                        name=f"{user.name__given}'s Organization",
                        description=f"{user.name__given}'s Organization",
                        business_name=f"{user.name__given}",
                        system_entity=True,
                        active=True,
                        system_tag=['system'],
                        status='SETUP',
                    ))
                    await self.insert(org_record)
                    organization = org_record

                org_id = organization._id

                profile_record = self.create('profile', dict(
                    _id=UUID_GENR(),
                    user_id=user_id,
                    name__family=user.name__family,
                    name__given=user.name__given,
                    name__middle=user.name__middle,
                    name__prefix=user.name__prefix,
                    name__suffix=user.name__suffix,
                    telecom__email=user.telecom__email,
                    telecom__phone=user.telecom__phone,
                    status='ACTIVE',
                    current_profile=True,
                    organization_id=org_id,
                    _realm=config.REALM
                ))
                await self.insert(profile_record)

                profile_role_record = self.create('profile_role', dict(
                    _id=UUID_GENR(),
                    profile_id=profile_record._id,
                    role_key='OWNER',
                    role_source='SYSTEM',
                    _realm=config.REALM
                ))
                await self.insert(profile_role_record)

                profile_status = self.create('profile_status', dict(
                    _id=UUID_GENR(),
                    profile_id=profile_record._id,
                    src_state=profile_record.status,
                    dst_state=profile_record.status,
                    _realm=config.REALM
                ))
                await self.insert(profile_status)
                profile = profile_record
            else:
                curr_profile = curr_profile
                profile = curr_profile

                if self._active_profile:
                    act_profile = await self.exist('profile', identifier=self._active_profile._id)
                    if not act_profile:
                        raise UnauthorizedError('U100-401', f'Active profile [{self._active_profile}] not found!')

                    if curr_profile._id != act_profile._id:
                        await self.update_one('profile', identifier=curr_profile._id, current_profile=False)
                        await self.update_one('profile', identifier=act_profile._id, current_profile=True)

                    profile = act_profile

                organization = await self.fetch('organization', profile.organization_id)

        # ---------- Realm/Roles ----------
        iamroles = auth_user.realm_access['roles']
        # realm = str(auth_user.iss).rsplit("/", 1)[1]
        realm = config.REALM

        # ---------- Auth Context ----------
        return AuthorizationContext(
            realm = realm,
            user = user,
            profile = profile,
            organization = organization,
            iamroles = iamroles
        )
