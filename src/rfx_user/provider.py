from .state import IDMStateManager
from types import SimpleNamespace
from fluvius.fastapi.auth import FluviusAuthProfileProvider, TokenPayload
from fluvius.auth import AuthorizationContext
from fluvius.error import UnauthorizedError


class RFXAuthProfileProvider(FluviusAuthProfileProvider):
    def user_data(self, data):
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
        self._manager = IDMStateManager(app)
        self._active_profile = active_profile
        """ Lookup services for user related info """

    async def get_auth_context(self, user_claims):
        self._claims = TokenPayload(**user_claims)
        return AuthorizationContext(
            realm='default',
            user=await self.get_user(),
            profile=await self.get_profile(),
            organization=await self.get_organization(),
            iam_roles=await self.get_iamroles()
        )

    async def get_user(self):
        if hasattr(self, '_user'):
            return self._user

        user_id = self._claims.sub
        user_data = self.user_data(self._claims)
        user_record = await self._manager.find_one('user', identifier=self._claims.sub)

        if not user_record:
            await self._manager.insert(self.create('user', user_data))
        else:
            await self._manager.update_one('user', identifier=user_id, **user_data)

        self._user = await self._manager.find_one('user', identifier=user_id)
        return self._user

    async def get_profile(self):
        if not hasattr(self, '_profile'):
            q = dict(where=dict(user_id=self._claims.sub, current_profile=True, status='ACTIVE'))
            current_profile = await self._manager.find_all('profile', q)
            if not current_profile:
                self._profile = SimpleNamespace(_id=self._claims.sub)

            current_profile = current_profile[0]
            self._profile = current_profile

            if self._active_profile:
                active_profile = await self._manager.find_one('profile', identifier=self._active_profile)
                if not active_profile:
                    raise UnauthorizedError('U100-401', f'Active profile [{self._active_profile}] not found!')

                self._profile = active_profile
                if current_profile._id != active_profile._id:
                    await self._manager.update_one('profile', identifier=current_profile._id, current_profile=False)
                    await self._manager.update_one('profile', identifier=active_profile._id, current_profile=True)

        return self._profile

    async def get_organization(self):
        if not hasattr(self, '_organization'):
            if not getattr(self._profile, 'organization_id', None):
                self._organization = SimpleNamespace(_id=self._claims.sub)
            else:
                self._organization = await self._manager.fetch('organization', self._profile.organization_id)

        return self._organization

    async def get_iamroles(self):
        if not hasattr(self, '_iamroles'):
            self._iamroles = self._claims.realm_access['roles']
            
        ''' Identity and Access Management Roles '''
        return self._iamroles
