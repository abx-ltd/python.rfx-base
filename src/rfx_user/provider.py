from types import SimpleNamespace
from fluvius.data import DataAccessManager
from fluvius.auth import AuthorizationContext
from fluvius.fastapi.auth import FluviusAuthProfileProvider, KeycloakTokenPayload
from fluvius.fastapi import config

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

    def __init__(self, app):
        """ Lookup services for user related info """
        super(DataAccessManager, self).__init__(app)

    async def setup_context(self, auth_user: KeycloakTokenPayload) -> AuthorizationContext:
        user_id = auth_user.sub
        profile = SimpleNamespace(
            _id=auth_user.jti,
            name=auth_user.name,
            roles=('user', 'staff', 'provider')
        )

        organization = SimpleNamespace(
            _id=auth_user.sub,
            name=auth_user.family_name
        )
        iamroles = auth_user.realm_access['roles']
        realm = str(auth_user.iss).rsplit("/", 1)[1]

        user_data = self.format_user_data(auth_user)
        user_record = await self.find_one('user', identifier=user_id)

        if not user_record:
            await self.insert_one('user', user_data)
        else:
            await self.update_one('user', user_id, **user_data)

        return AuthorizationContext(
            realm = realm,
            user = auth_user,
            profile = profile,
            organization = organization,
            iamroles = iamroles
        )

    # async def get_auth_context(self, user_claims):
    #     user_id = user_claims.sub
    #     user_data = self.user_data(user_claims)
    #     user_record = await self.find_one('user', identifier=user_id)

    #     if not user_record:
    #         await self.insert(self.create('user', user_data))
    #     else:
    #         await self.update_one('user', identifier=user_id, **user_data)

    #     user = await self.find_one('user', identifier=user_id)

    #     profile = SimpleNamespace(
    #         _id=user_data.jti,
    #         name=user_data.name,
    #         roles=('user', 'staff', 'provider')
    #     )

    #     organization = SimpleNamespace(
    #         _id=user_data.sub,
    #         name=user_data.family_name
    #     )
    #     iamroles = ('user', 'staff', 'provider')
    #     realm = 'default'
    #         # dict(
    #         #     realm_access=self._claims.realm_access,
    #         #     resource_access=self._claims.resource_access,
    #         # )
    #     return AuthorizationContext(
    #         realm = realm,
    #         user = user,
    #         profile = profile,
    #         organization = organization,
    #         iamroles = iamroles
    #     )
