from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action


class RFXHatchetAggregate(Aggregate):
    @action("hatchet-workflow-run-removed", resources="hatchet_workflow_run")
    async def remove_hatchet_workflow_run(self):
        """Action to handle the removal of a hatchet workflow run."""
        hatchet_workflow_run = self.rootobj
        await self.statemgr.invalidate(hatchet_workflow_run)
