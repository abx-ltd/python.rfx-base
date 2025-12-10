from fluvius.domain.state import DataAccessManager
from rfx_schema import RFXUserConnector

class IDMStateManager(DataAccessManager):
    __connector__ = RFXUserConnector
    __automodel__ = True

    async def _add_entry(self, model, **data):
        entry = self.create(model, **data)
        await self.insert(entry)
        return entry

    async def add_entry(self, model, **data):
        return await self._add_entry(model, **data)
