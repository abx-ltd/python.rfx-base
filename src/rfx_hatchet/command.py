from .domain import RFXHatchetDomain

processor = RFXHatchetDomain.command_processor
Command = RFXHatchetDomain.Command


class RemoveHatchetWorkflowRun(Command):
    """Remove Hatchet Workflow Run - Removes a hatchet workflow run"""

    class Meta:
        key = "remove-hatchet-workflow-run"
        resources = ("hatchet_workflow_run",)
        tags = ["hatchet", "workflow", "run", "remove"]
        auth_required = True
        description = "Remove hatchet workflow run"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Remove hatchet workflow run"""
        await agg.remove_hatchet_workflow_run()
