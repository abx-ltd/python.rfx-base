from fluvius.domain.state import DataAccessManager
from rfx_schema import RFXNotifyConnector


class NotifyStateManager(DataAccessManager):
    __connector__ = RFXNotifyConnector
    __automodel__ = True

    async def _add_entry(self, model, **data):
        entry = self.create(model, **data)
        await self.insert(entry)
        return entry

    async def add_notification_log(self, **data):
        return await self._add_entry('notification_delivery_log', **data)
