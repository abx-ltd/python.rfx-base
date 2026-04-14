from fluvius.query import DomainQueryManager
from fluvius.hatchet.tracker import HatchetWorkflowTracker
from fluvius.query import DomainQueryResource
from fluvius.query.field import StringField, DatetimeField
from datetime import datetime
from .domain import RFXHatchetDomain
from .state import RFXHatchetStateManager


class RFXHatchetQueryManager(DomainQueryManager):
    __data_manager__ = RFXHatchetStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXHatchetDomain.Meta.namespace
        tags = RFXHatchetDomain.Meta.tags


resource = RFXHatchetQueryManager.register_resource
endpoint = RFXHatchetQueryManager.register_endpoint


@resource("hatchet_workflow_run")
class HatchetWorkflowRunQuery(DomainQueryResource):
    """Hatchet workflow run queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_hatchet_workflow_run"

    workflow_name: str = StringField("Workflow Name")
    workflow_run_id: str = StringField("Workflow Run ID")
    labels: str = StringField("Labels")
    args: str = StringField("Args")
    kwargs: str = StringField("Kwargs")
    status: str = StringField("Status")
    start_time: datetime = DatetimeField("Start Time")
    end_time: datetime = DatetimeField("End Time")
    result: str = StringField("Result")
    err_message: str = StringField("Error Message")
    err_trace: str = StringField("Error Trace")
