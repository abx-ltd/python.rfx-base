from fluvius.data import DataModel, logger, serialize_mapping
from .domain import RFXClientDomain
from . import config
    
from cpo_portal.integration import get_worker_client
from .service import LinearService


class DiscussionMessageData(DataModel):
    command: str = "create-ticket"
    payload: dict = {}
    ticket_id: str = None
    context: dict = {}


class DiscussionMessage(RFXClientDomain.Message):
    Data = DiscussionMessageData

    async def _dispatch(msg):
        data = msg.data

        await get_worker_client().request(
            f"{config.DISCUSSION_NAMESPACE}:{data.command}",
            command=data.command,
            resource="ticket",
            identifier=str(data.ticket_id),
            payload=serialize_mapping(data.payload),
            _headers={},
            _context=dict(
                source="internal",
                audit=data.context,
            )
        )


class ProjectMessageData(DataModel):
    command: str = "add-ticket-to-project"
    payload: dict = {}
    project_id: str = None
    context: dict = {}


class ProjectMessage(RFXClientDomain.Message):
    Data = ProjectMessageData

    async def _dispatch(msg):
        data = msg.data

        await get_worker_client().send(
            f"{config.NAMESPACE}:{data.command}",
            command=data.command,
            resource="project",
            identifier=str(data.project_id),
            payload=serialize_mapping(data.payload),
            _headers={},
            _context=dict(
                source="internal",
                audit=data.context,
            )
        )


class NotiMessageData(DataModel):
    command: str = "send-message"
    payload: dict = {}
    context: dict = {}


class NotiMessage(RFXClientDomain.Message):
    Data = NotiMessageData

    async def _dispatch(msg):
        data = msg.data

        await get_worker_client().send(
            f"{config.MESSAGE_NAMESPACE}:{data.command}",
            command=data.command,
            resource="message",
            payload=serialize_mapping(data.payload),
            _headers={},
            _context=dict(
                audit=data.context,
            )
        )


class LinearMessageData(DataModel):
    command: str = "sync-project-integration"
    payload: dict = {}
    project: dict = {}
    project_id: str = None
    context: dict = {}


class LinearMessage(RFXClientDomain.Message):
    Data = LinearMessageData

    async def _dispatch(msg):
        data = msg.data

        check = LinearService.check_project_exists(data.project_id)
        exists = check.get("exists", False)
        
        url = None
        if not exists:
            linear_result = LinearService.create_project(data.project)
            url = (
                linear_result
                .get("result", {})
                .get("data", {})
                .get("projectCreate", {})
                .get("project", {})
                .get("url")
            )
        else:
            linear_result = LinearService.update_project(data.project)
            url = (
                linear_result
                .get("result", {})
                .get("data", {})
                .get("projectUpdate", {})
                .get("project", {})
                .get("url")
            )

        data.payload["external_url"] = url


        await get_worker_client().send(
            f"{config.NAMESPACE}:{data.command}",
            command=data.command,
            resource="project",
            identifier=str(data.project_id),
            payload=serialize_mapping(data.payload),
            _headers={},
            _context=dict(
                source="internal",
                audit=data.context,
            )
        )
