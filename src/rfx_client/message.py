from fluvius.data import DataModel, logger
from .domain import RFXClientDomain
from . import config
from fluvius.data import serialize_mapping

from cpo_portal.integration import get_worker_client


class DiscussionMessageData(DataModel):
    command: str = "create-ticket"
    payload: dict = {}
    ticket_id: str = None
    context: dict = {}


class DiscussionMessage(RFXClientDomain.Message):
    Data = DiscussionMessageData

    async def _dispatch(msg):
        data = msg.data
        logger.info(f"DiscussionMessage: {data}")

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
        logger.info(f"ProjectMessage: {data}")

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
        logger.info(f"NotiMessage: {data}")

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
