from .model import IDMConnector
from fluvius.fastapi.auth import FluviusAuthProfileProvider, TokenPayload
from fluvius.fastapi import config
from fluvius.data import DataAccessManager


class RFXAuthProfileProvider(
    FluviusAuthProfileProvider,
    DataAccessManager
):
    __connector__ = IDMConnector
    __auto_model__ = True

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

    def __init__(self, user_claims, active_profile=None):
        """ Lookup services for user related info """

        self._claims = TokenPayload(**user_claims)
        DataAccessManager.__init__(self, None)

    async def get_user(self):
        if hasattr(self, '_user'):
            return self._user

        user_id = self._claims.sub
        user_data = self.user_data(self._claims)
        user_record = await self.find_one('user', identifier=self._claims.sub)

        if not user_record:
            await self.insert(self.create('user', user_data))
        else:
            await self.update_one('user', identifier=user_id, **user_data)

        self._user = await self.find_one('user', identifier=user_id)
        return self._user

    async def get_profile(self):
        if not hasattr(self, '_profile'):
            self._profile = None
        return self._profile

    async def get_organization(self):
        if not hasattr(self, '_organization'):
            self._organization = None
        return self._organization

    async def get_iamroles(self):
        if not hasattr(self, '_iamroles'):
            self._iamroles = dict(
                realm_access=self._claims.realm_access,
                resource_access=self._claims.resource_access,
            )
        ''' Identity and Access Management Roles '''
        return self._iamroles
