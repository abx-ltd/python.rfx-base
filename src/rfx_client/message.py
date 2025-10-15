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
        
        logger.info(f"[Linear] Project exists: {exists}")
        
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
            
        logger.info(f"[Linear] Sync project result: {linear_result}")

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

\

class CreateLinearMessageData(DataModel):
    command: str = "create-project-integration"
    payload: dict = {}
    project: dict = {}
    project_id: str = None
    context: dict = {}
    
class CreateLinearMessage(RFXClientDomain.Message):
    Data = CreateLinearMessageData

    async def _dispatch(msg):
        data = msg.data
        
        check = LinearService.check_project_exists(data.project_id)
    
        exists = check.get("exists", False)
        
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
            raise ValueError(f"Project already exists in Linear: {data.project_id}")
            
        
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

# ---------- Update ----------
class UpdateLinearMessageData(DataModel):
    command: str = "update-project-integration"
    payload: dict = {}
    project: dict = {}
    project_id: str = None
    context: dict = {}
    
class UpdateLinearMessage(RFXClientDomain.Message):
    Data = UpdateLinearMessageData

    async def _dispatch(msg):
        data = msg.data
        
        check = LinearService.check_project_exists(data.project_id)
    
        exists = check.get("exists", False)
        
        if exists:
            linear_result = LinearService.update_project(data.project)
            url = (
                linear_result
                .get("result", {})
                .get("data", {})
                .get("projectUpdate", {})
                .get("project", {})
                .get("url")
            )
        else:
            raise ValueError(f"Project does not exist in Linear: {data.project_id}")
            
        
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

# ---------- Remove ----------
class RemoveLinearMessageData(DataModel):
    command: str = "remove-project-integration"
    payload: dict = {}
    project_id: str = None
    context: dict = {}

class RemoveLinearMessage(RFXClientDomain.Message):
    Data = RemoveLinearMessageData

    async def _dispatch(msg):
        data = msg.data
        
        check = LinearService.check_project_exists(data.project_id)
    
        exists = check.get("exists", False)
        
        if exists:
            linear_result = LinearService.delete_project(data.project_id)
            logger.info(f"[Linear] Delete project result: {linear_result}")
        else:
            raise ValueError(f"Project does not exist in Linear: {data.project_id}")
        


        logger.info(f"Payload: {data.payload}, project_id: {data.project_id}")

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
    
    
    
#-------------Project Milestone Messages----------------#
class CreateMilestoneMessageData(DataModel):
    command: str = "create-project-milestone-integration"
    payload: dict = {}
    milestone: dict = {}
    project_id: str = None
    context: dict = {}
class CreateMilestoneMessage(RFXClientDomain.Message):
    Data = CreateMilestoneMessageData

    async def _dispatch(msg):
        data = msg.data
        
        logger.info(f"[Linear] Creating milestone for project {data.project_id}")
        check_milestone = LinearService.check_milestone_exists(data.milestone.get("_id"))
        logger.info(f"milestone_id: {data.milestone.get('_id')}, check_milestone: {check_milestone}")
        if check_milestone.get("exists", False):
            raise ValueError(f"Milestone already exists in Linear: {data.milestone.get('_id')}")
        
        linear_result = LinearService.create_milestone(data.milestone)
        
        logger.info(f"[Linear] Create milestone result: {linear_result}")
        
        url= LinearService.get_project_url(data.project_id)
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


class UpdateMilestoneMessageData(DataModel):
    command: str = "update-project-milestone-integration"
    payload: dict = {}
    milestone: dict = {}
    project_id: str = None
    context: dict = {}
    
class UpdateMilestoneMessage(RFXClientDomain.Message):
    Data = UpdateMilestoneMessageData

    async def _dispatch(msg):
        data = msg.data
        
        logger.info(f"[Linear] Updating milestone for project {data.project_id}")
        check_milestone = LinearService.check_milestone_exists(data.milestone.get("_id"))
        
        if not check_milestone.get("exists", False):
            raise ValueError(f"Milestone does not exist in Linear: {data.milestone.get('_id')}")
        
        linear_result = LinearService.update_milestone(data.milestone)
        
        logger.info(f"[Linear] Update milestone result: {linear_result}")
        
        url = LinearService.get_project_url(data.project_id)
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


class RemoveMilestoneMessageData(DataModel):
    command: str = "remove-project-milestone-integration"
    payload: dict = {}
    milestone_id: str = None
    project_id: str = None
    context: dict = {}


class RemoveMilestoneMessage(RFXClientDomain.Message):
    Data = RemoveMilestoneMessageData

    async def _dispatch(msg):
        data = msg.data

        logger.info(f"[Linear] Removing milestone for project {data.project_id}")
        check_milestone = LinearService.check_milestone_exists(data.milestone_id)
        
        if not check_milestone.get("exists", False):
            raise ValueError(f"Milestone does not exist in Linear: {data.milestone_id}")
        
        linear_result = LinearService.delete_milestone(data.milestone_id)
        
        logger.info(f"[Linear] Delete milestone result: {linear_result}")
        
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
    


        
    
        
        
