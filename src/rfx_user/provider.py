from .auth import FluviusAuthProfileProvider
from .model import IDMConnector
from fluvius.data import DataAccessManagerBase


class RFXAuthProfileProvier(FluviusAuthProfileProvider, DataAccessManagerBase):
    __connector__ = IDMConnector

    """ Lookup services for user related info """
    def __init__(self, user_claims, active_profile=None):
        self._claims = TokenPayload(**user_claims)

    async def get_user(self):
        if not hasattr(self, '_user'):
            self._user = await self.fetch('user', identifier=self._claims.jti)
        return self._user

    async def get_profile(self):
        if not hasattr(self, '_profile'):
            self._profile = await self.fetch('profile', identifier=self._claims.jti)
        return self._profile

    async def get_organization(self):
        if not hasattr(self, '_organization'):
            self._organization = await self.fetch('organization', identifier=self._claims.jti)
        return self._organization

    async def get_iamroles(self):
        ''' Identity and Access Management Roles '''
        return self._iamroles
