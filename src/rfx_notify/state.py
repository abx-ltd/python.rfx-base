from fluvius.domain.state import DataAccessManager
from .model import NotifyConnector


class NotifyStateManager(DataAccessManager):
    __connector__ = NotifyConnector
    __automodel__ = True

    async def _add_entry(self, model, **data):
        entry = self.create(model, **data)
        await self.insert(entry)
        return entry

    async def add_notification_log(self, **data):
        return await self._add_entry('notification_delivery_log', **data)
