from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping
from .types import OrganizationStatus

class UserProfileAggregate(Aggregate):
    async def set_org_status(self, org, status, note=None):
        record = self.init_resource("organization-status",
            organization_id=org._id,
            src_state=org.status,
            dst_state=status,
            note=note
        )
        await self.statemgr.insert(record)

    @action("organization-created", resources="organization", emit_event=True)
    async def create_organization(self, stm, /, data):
        record = self.init_resource(
            "organization",
            serialize_mapping(data),
            _id=self.aggroot.identifier,
            status=getattr(data, "status", "SETUP")
        )
        await stm.insert(record)
        await self.set_org_status(record, record.status)
        return record

    @action("organization-updated", resources="organization", emit_event=True)
    async def update_organization(self, stm, /, data):
        item = self.rootobj
        await stm.update_record(item, serialize_mapping(data))
        if getattr(data, "status", None) and item.status != data.status:
            await self.set_org_status(item, data.status)

        return item

    @action("organization-updated", resources="organization")
    async def deactivate_organization(self, stm, /, data=None):
        item = self.rootobj
        await stm.update_record(item, dict(status=OrganizationStatus.INACTIVE))
        await self.set_org_status(item, OrganizationStatus.INACTIVE)
