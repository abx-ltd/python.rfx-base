from fluvius.data import DataModel, logger
from .domain import CPOPortalDomain
from . import config
from fluvius.data import serialize_mapping

from cpo_portal.integration import get_worker_client


class DiscussionMessageData(DataModel):
    command: str = "create-ticket"
    payload: dict = {}
    ticket_id: str = None  # Added missing field
    context: dict = {}     # Added missing field


class DiscussionMessage(CPOPortalDomain.Message):
    Data = DiscussionMessageData

    async def _dispatch(msg):
        data = msg.data
        logger.info(f"DiscussionMessage: {data}")

        await get_worker_client().request(
            f"rfx-discussion:{data.command}",
            command=data.command,
            resource="ticket",
            identifier=str(data.ticket_id),
            payload=serialize_mapping(data.payload),
            _headers={},
            _context=dict(
                source="internal",
                **data.context
            )
        )


class ProjectMessageData(DataModel):
    command: str = "add-ticket-to-project"
    payload: dict = {}
    project_id: str = None
    context: dict = {}     # Added missing field


class ProjectMessage(CPOPortalDomain.Message):
    Data = ProjectMessageData

    async def _dispatch(msg):

        data = msg.data
        logger.info(f"ProjectMessage: {data}")

        await get_worker_client().request(
            f"cpo-portal:{data.command}",
            command=data.command,
            resource="project",
            identifier=str(data.project_id),
            payload=serialize_mapping(data.payload),
            _headers={},
            _context=dict(
                source="internal",
                **data.context
            )
        )
