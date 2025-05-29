from types import SimpleNamespace
from fluvius.data import DataAccessManager
from fluvius.auth import AuthorizationContext
from fluvius.fastapi.auth import FluviusAuthProfileProvider, KeycloakTokenPayload
from fluvius.error import UnauthorizedError

from .model import IDMConnector

class RFXAuthProfileProvider(
    FluviusAuthProfileProvider,
    DataAccessManager
):
    __connector__ = IDMConnector
    __automodel__ = True

    def format_user_data(self, data):
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
        """ Lookup services for user related info """
        super(DataAccessManager, self).__init__(app)
        self._active_profile = active_profile

    async def setup_context(self, auth_user: KeycloakTokenPayload) -> AuthorizationContext:
        # ---------- User ----------
        user_id = auth_user.sub
        user_data = self.format_user_data(auth_user)
        await self.upsert('user', user_data)
        user = await self.fetch('user', user_id)

        # ---------- Proifle ----------
        q = dict(where=dict(user_id=user_id, current_profile=True, status='ACTIVE'), limit=1)
        curr_profile = await self.query('profile', q)

        if not curr_profile:
            profile = SimpleNamespace(_id=auth_user.sub)
            organization = SimpleNamespace(_id=self._claims.sub)
        else:
            curr_profile = curr_profile[0]
            profile = curr_profile

            if self._active_profile:
                act_profile = await self.find_one('profile', self._active_profile)
                if not act_profile:
                    raise UnauthorizedError('U100-401', f'Active profile [{self._active_profile}] not found!')

                if curr_profile._id != act_profile._id:
                    await self.update_one('profile', identifier=curr_profile._id, current_profile=False)
                    await self.update_one('profile', identifier=act_profile._id, current_profile=True)

                profile = act_profile

            organization = await self.fetch('organization', profile.organization_id)

        # ---------- Realm/Roles ----------
        iamroles = auth_user.realm_access['roles']
        realm = str(auth_user.iss).rsplit("/", 1)[1]

        # ---------- Auth Context ----------
        return AuthorizationContext(
            realm = realm,
            user = user,
            profile = profile,
            organization = organization,
            iamroles = iamroles
        )
