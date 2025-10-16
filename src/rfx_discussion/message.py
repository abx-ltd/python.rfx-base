from fluvius.data import DataModel, logger, serialize_mapping
from .domain import RFXDiscussionDomain
from . import config

from cpo_portal.integration import get_worker_client
from .service import LinearService





#------------Create Ticket Integration Message----------------#

class SyncTicketToLinearMessageData(DataModel):
    command: str = "sync-ticket-integration"
    payload: dict = {}
    ticket: dict = {}
    ticket_id: str = None
    project_id: str = None
    context: dict = {}
    
class SyncTicketToLinearMessage(RFXDiscussionDomain.Message):
    Data = SyncTicketToLinearMessageData

    async def _dispatch(msg):
        data = msg.data

        check = LinearService.check_issue_exists(data.ticket.get("_id"))

        if not check.get("exists", False):
            project_id = data.project_id
            linear_result = LinearService.create_issue(data.ticket, project_id, data.ticket_id)
            logger.info(f"[Linear] Create issue result: {linear_result}")
            issue_create_result = linear_result.get("result", {}).get("data", {}).get("issueCreate", {})
            issue_data = issue_create_result.get("issue", {})
        else:
            linear_result = LinearService.update_issue(data.ticket, data.ticket_id)
            logger.info(f"[Linear] Update issue result: {linear_result}")
            issue_update_result = linear_result.get("result", {}).get("data", {}).get("issueUpdate", {})
            issue_data = issue_update_result.get("issue", {})

        
        
        
        
        url = issue_data.get("url")
        data.payload["external_url"] = url
        data.payload["external_id"] = issue_data.get("id")
        logger.info(f"[Linear] Issue URL: {url}, ID: {issue_data.get('id')}")
        
        await get_worker_client().send(
            f"{config.NAMESPACE}:{data.command}",
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


class CreateTicketIntegrationMessageData(DataModel):
    command: str = "create-ticket-integration"
    payload: dict = {}
    ticket: dict = {}
    ticket_id: str = None
    context: dict = {}

class CreateTicketIntegrationMessage(RFXDiscussionDomain.Message):
    Data = CreateTicketIntegrationMessageData

    async def _dispatch(msg):
        data = msg.data

        check = LinearService.check_issue_exists(data.ticket.get("_id"))

        if check.get("exists", False):
            raise ValueError(f"Ticket already exists in Linear: {data.ticket_id}")
        
        project_id = data.ticket.get("project_id")
        linear_result = LinearService.create_issue(data.ticket, project_id, data.ticket_id)
        logger.info(f"[Linear] Create issue result: {linear_result}")
        issue_create_result = linear_result.get("result", {}).get("data", {}).get("issueCreate", {})


        issue_data = issue_create_result.get("issue", {})
        url = issue_data.get("url")
        data.payload["external_url"] = url
        data.payload["external_id"] = issue_data.get("id")
        logger.info(f"[Linear] Issue URL: {url}, ID: {issue_data.get('id')}")
        
        await get_worker_client().send(
            f"{config.NAMESPACE}:{data.command}",
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


class UpdateTicketIntegrationMessageData(DataModel):
    command: str = "update-ticket-integration"
    payload: dict = {}
    ticket: dict = {}
    ticket_id: str = None
    context: dict = {}
    
class UpdateTicketIntegrationMessage(RFXDiscussionDomain.Message):
    Data = UpdateTicketIntegrationMessageData

    async def _dispatch(msg):
        data = msg.data

        check = LinearService.check_issue_exists(data.ticket.get("_id"))

        if not check.get("exists", False):
            raise ValueError(f"Ticket does not exist in Linear: {data.ticket_id}")
        
        
        linear_result = LinearService.update_issue(data.ticket, data.ticket_id)
        logger.info(f"[Linear] Update issue result: {linear_result}")

        issue_update_result = linear_result.get("result", {}).get("data", {}).get("issueUpdate", {})

        issue_data = issue_update_result.get("issue", {})
        url = issue_data.get("url")
        data.payload["external_url"] = url
        data.payload["external_id"] = issue_data.get("id")
        logger.info(f"[Linear] Issue URL: {url}, ID: {issue_data.get('id')}")
        
        await get_worker_client().send(
            f"{config.NAMESPACE}:{data.command}",
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
        
        
class RemoveTicketIntegrationMessageData(DataModel):
    command: str = "remove-ticket-integration"
    payload: dict = {}
    ticket: dict = {}
    ticket_id: str = None
    context: dict = {}
    
class RemoveTicketIntegrationMessage(RFXDiscussionDomain.Message):
    Data = RemoveTicketIntegrationMessageData

    async def _dispatch(msg):
        data = msg.data

        check = LinearService.check_issue_exists(data.ticket.get("_id"))

        if not check.get("exists", False):
            raise ValueError(f"Ticket does not exist in Linear: {data.ticket_id}")
        
        
        linear_result = LinearService.delete_issue(data.ticket_id)
        logger.info(f"[Linear] Delete issue result: {linear_result}")
        
        await get_worker_client().send(
            f"{config.NAMESPACE}:{data.command}",
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