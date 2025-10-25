from ..base import (
    PMService, 
    CreateTicketPayload, CreateTicketResponse,
    UpdateTicketPayload, UpdateTicketResponse,
    # CreateCommentPayload, CreateCommentResponse,
    # UpdateCommentPayload, UpdateCommentResponse,
    CreateProjectPayload, CreateProjectResponse,  
    UpdateProjectPayload, UpdateProjectResponse,
    CreateProjectMilestonePayload, CreateProjectMilestoneResponse,
    UpdateProjectMilestonePayload, UpdateProjectMilestoneResponse,
    CreateCommentPayload, CreateCommentResponse,
    UpdateCommentPayload, UpdateCommentResponse,
)
from .linear_app.integration import (
    LinearIntegration,
    get_linear_status_id,
    get_linear_user_id,
    get_linear_label_id,
    map_priority
)
from typing import Dict, Any, Optional
from fluvius.data import logger

from ..._meta import config as _config


class LinearProvider(PMService):
    """Linear Project Management Integration via UAPI with httpx"""
    
    PROVIDER_NAME = "linear"
    
    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.team_id = _config.LINEAR_TEAM_ID
        self._client = LinearIntegration()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close httpx client"""
        await self._client.close()
    
    async def create_ticket(self, payload: CreateTicketPayload) -> CreateTicketResponse:
        """Create issue in Linear via UAPI"""
        
        # Build Linear-specific payload
        linear_data = {
            "title": payload.title,
            "teamId": payload.team_id or self.team_id,
        }
        
        # Optional: use your internal ticket ID as Linear issue ID
        if hasattr(payload, 'ticket_id') and payload.ticket_id:
            linear_data["id"] = str(payload.ticket_id)
        
        if payload.description:
            linear_data["description"] = payload.description
        
        if payload.priority is not None:
            # If priority is string, convert it
            if isinstance(payload.priority, str):
                linear_data["priority"] = map_priority(payload.priority)
            else:
                linear_data["priority"] = payload.priority
        
        # Map status to Linear state ID
        if payload.status_id:
            state_id = get_linear_status_id(payload.status_id)
            if state_id:
                linear_data["stateId"] = state_id
        
        # Map assignee to Linear user ID
        if payload.assignee_id:
            assignee_id = get_linear_user_id(payload.assignee_id)
            if assignee_id:
                linear_data["assigneeId"] = assignee_id
        
        # Map labels to Linear label IDs
        if payload.labels:
            label_ids = []
            for label in payload.labels:
                label_id = get_linear_label_id(label)
                if label_id:
                    label_ids.append(label_id)
            if label_ids:
                linear_data["labelIds"] = label_ids
        
        # Project ID
        if payload.project_id:
            linear_data["projectId"] = str(payload.project_id)
        
        try:
            logger.info(f"[Linear] Creating issue with data: {linear_data}")
            result = await self._client.create_issue(linear_data)
            
            return CreateTicketResponse(
                external_id=result.get('id'),
                url=result.get('url'),
                title=result.get('title'),
                status=result.get('state', {}).get('name')
            )
        except Exception as e:
            logger.error(f"Failed to create Linear issue: {str(e)}")
            raise
    
    async def update_ticket(self, payload: UpdateTicketPayload) -> UpdateTicketResponse:
        """Update issue in Linear via UAPI"""
        
        update_data = {}
        
        if payload.title:
            update_data["title"] = payload.title
        
        if payload.description:
            update_data["description"] = payload.description
        
        if payload.status_id:
            state_id = get_linear_status_id(payload.status_id)
            if state_id:
                update_data["stateId"] = state_id
        
        if payload.assignee_id:
            assignee_id = get_linear_user_id(payload.assignee_id)
            if assignee_id:
                update_data["assigneeId"] = assignee_id
        
        if payload.priority is not None:
            if isinstance(payload.priority, str):
                update_data["priority"] = map_priority(payload.priority)
            else:
                update_data["priority"] = payload.priority
        
        try:
            logger.info(f"[Linear] Updating issue {payload.external_id} with data: {update_data}")
            result = await self._client.update_issue(
                issue_id=payload.external_id,
                data=update_data
            )
            
            return UpdateTicketResponse(
                external_id=payload.external_id,
                updated=result.get('success', False),
                external_url=result.get('issue', {}).get('url')
            )
        except Exception as e:
            logger.error(f"Failed to update Linear issue: {str(e)}")
            raise
    
    async def delete_ticket(self, external_id: str, permanently: bool = True) -> bool:
        """Delete issue in Linear via UAPI"""
        try:
            result = await self._client.delete_issue(external_id, permanently)
            return result.get('success', False)
        except Exception as e:
            logger.error(f"Failed to delete Linear issue: {str(e)}")
            return False
    
    async def get_ticket(self, external_id: str) -> Dict[str, Any]:
        """Get issue from Linear via UAPI"""
        try:
            return await self._client.get_issue(external_id)
        except Exception as e:
            logger.error(f"Failed to get Linear issue: {str(e)}")
            raise
    
    async def check_ticket_exists(self, external_id: str) -> Dict[str, Any]:
        """Check if ticket exists in Linear"""
        return await self._client.check_issue_exists(external_id)
    
    
    #========= Project Operations ==========
    async def create_project(self, payload: CreateProjectPayload) -> CreateProjectResponse:
       
        linear_data = {
            "name": payload.name,
            "teamIds": [payload.team_id] if payload.team_id else [self.team_id],
            "id": str(payload.project_id) if payload.project_id else None
        }
        
        if payload.description:
            linear_data["description"] = payload.description
        
        if payload.lead_id:
            linear_user_id = get_linear_user_id(str(payload.lead_id))
            if linear_user_id:
                linear_data["leadId"] = linear_user_id
        
        if payload.color:
            linear_data["color"] = payload.color
        
        if payload.icon:
            linear_data["icon"] = payload.icon
        
        if payload.state:
            # Map internal state to Linear state
            state_map = {
                "PLANNED": "planned",
                "STARTED": "started",
                "IN_PROGRESS": "started",
                "PAUSED": "paused",
                "COMPLETED": "completed",
                "CANCELED": "canceled",
                "DRAFT": "planned",  
            }
            linear_data["state"] = state_map.get(payload.state.upper(), "planned")
        
        if payload.start_date:
            linear_data["startDate"] = payload.start_date
        
        if payload.target_date:
            linear_data["targetDate"] = payload.target_date
        
        try:
            logger.info(f"[Linear] Creating project: {linear_data}")
            result = await self._client.create_project(linear_data)
            
            return CreateProjectResponse(
                external_id=result.get('id'),
                url=result.get('url'),
                name=result.get('name'),
                state=result.get('state')
            )
        except Exception as e:
            logger.error(f"Failed to create Linear project: {str(e)}")
            raise    


    async def update_project(self, payload: UpdateProjectPayload) -> UpdateProjectResponse:
        
        linear_data = {}
        
        if payload.name:
            linear_data["name"] = payload.name
        
        if payload.description:
            linear_data["description"] = payload.description
        
        if payload.lead_id:
            linear_user_id = get_linear_user_id(str(payload.lead_id))
            if linear_user_id:
                linear_data["leadId"] = linear_user_id
        
        if payload.state:
            state_map = {
                "PLANNED": "planned",
                "STARTED": "started",
                "IN_PROGRESS": "started",
                "PAUSED": "paused",
                "COMPLETED": "completed",
                "CANCELED": "canceled",
                "DRAFT": "planned",
            }
            linear_data["state"] = state_map.get(payload.state.upper())
        
        if payload.color:
            linear_data["color"] = payload.color
        
        if payload.target_date:
            linear_data["targetDate"] = payload.target_date
        
        try:
            logger.info(f"[Linear] Updating project {payload.external_id}")
            result = await self._client.update_project(payload.external_id, linear_data)
            
            return UpdateProjectResponse(
                external_id=result.get('id'),
                updated=True,
                external_url=result.get('url')
            )
        except Exception as e:
            logger.error(f"Failed to update Linear project: {str(e)}")
            raise


    async def delete_project(self, project_id: str, permanently: bool = False) -> bool:
        
        try:
            logger.info(f"[Linear] Deleting project: {project_id} (permanently={permanently})")
            
            # ✅ Call LinearIntegration client
            result = await self._client.delete_project(
                project_id=project_id,
                permanently=permanently
            )
            
            if result.get('success', False):
                logger.info(f"✓ Deleted Linear project: {project_id}")
                return True
            else:
                logger.warning(f"Failed to delete Linear project: {project_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete Linear project: {str(e)}")
            raise
        
    # ======== Project Milestone Operations ==========
    
    async def create_project_milestone(
        self, 
        payload: CreateProjectMilestonePayload
    ) -> CreateProjectMilestoneResponse:
        
        linear_data = {
            "name": payload.name,
            "projectId": payload.project_id,
        }
        
        if payload.description:
            linear_data["description"] = payload.description
        
        if payload.target_date:
            linear_data["targetDate"] = payload.target_date
        
        if payload.sort_order is not None:
            linear_data["sortOrder"] = payload.sort_order
        
        try:
            logger.info(f"[Linear] Creating milestone: {linear_data}")
            result = await self._client.create_project_milestone(linear_data)
            
            return CreateProjectMilestoneResponse(
                external_id=result.get('id'),
                name=result.get('name'),
                project_id=result.get('project', {}).get('id'),
                target_date=result.get('targetDate'),
                external_url=result.get('project', {}).get('url')
            )
        except Exception as e:
            logger.error(f"Failed to create Linear milestone: {str(e)}")
            raise
    
    async def update_project_milestone(
        self, 
        payload: UpdateProjectMilestonePayload
    ) -> UpdateProjectMilestoneResponse:
        
        linear_data = {}
        
        if payload.name:
            linear_data["name"] = payload.name
        
        if payload.description:
            linear_data["description"] = payload.description
        
        if payload.target_date:
            linear_data["targetDate"] = payload.target_date
        
        if payload.sort_order is not None:
            linear_data["sortOrder"] = payload.sort_order
        
        try:
            logger.info(f"[Linear] Updating milestone {payload.external_id}")
            result = await self._client.update_project_milestone(
                payload.external_id, 
                linear_data
            )
            
            return UpdateProjectMilestoneResponse(
                external_id=result.get('id', payload.external_id),
                updated=True,
                external_url=result.get('project', {}).get('url')
            )
        except Exception as e:
            logger.error(f"Failed to update Linear milestone: {str(e)}")
            raise
    
    async def delete_project_milestone(self, external_id: str) -> bool:
        """
        Delete project milestone in Linear
        
        Args:
            external_id: Linear milestone ID
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"[Linear] Deleting milestone: {external_id}")
            
            result = await self._client.delete_project_milestone(external_id)
            
            if result.get('success', False):
                logger.info(f"✓ Deleted Linear milestone: {external_id}")
                return True
            else:
                logger.warning(f"Failed to delete Linear milestone: {external_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete Linear milestone: {str(e)}")
            raise
    
    # ========== COMMENT OPERATIONS ==========
    
    async def create_comment(
        self, 
        payload: CreateCommentPayload
    ) -> CreateCommentResponse:
        """
        Create comment in Linear
        
        Args:
            payload: CreateCommentPayload with comment data
            
        Returns:
            CreateCommentResponse with external_id and URL
        """
        logger.info(f"payload in create_comment: {payload}")
        comment_data = {
                "body": payload.body,
                "issueId": payload.target_id
            }
        
        
        # Use internal comment ID if provided
        if payload.comment_id:
            comment_data["id"] = str(payload.comment_id)
        
        # Support nested comments
        if payload.parent_id:
            comment_data["parentId"] = str(payload.parent_id)
        
        try:
            logger.info(f"[Linear] Creating comment for issue: {payload.target_id}")
            result = await self._client.create_comment(comment_data)
            
            return CreateCommentResponse(
                external_id=result.get('id'),
                url=result.get('url'),
                body=result.get('body')
            )
        except Exception as e:
            logger.error(f"Failed to create Linear comment: {str(e)}")
            raise
    
    async def update_comment(
        self, 
        payload: UpdateCommentPayload
    ) -> UpdateCommentResponse:
        """
        Update comment in Linear
        
        Args:
            payload: UpdateCommentPayload with fields to update
            
        Returns:
            UpdateCommentResponse with external_id and updated status
        """
        try:
            logger.info(f"[Linear] Updating comment: {payload.external_id}")
            result = await self._client.update_comment(
                comment_id=payload.external_id,
                body=payload.body
            )
            
            return UpdateCommentResponse(
                external_id=payload.external_id,
                updated=result.get('success', False),
                url=result.get('comment', {}).get('url')
            )
        except Exception as e:
            logger.error(f"Failed to update Linear comment: {str(e)}")
            raise
    
    async def delete_comment(self, external_id: str) -> bool:
        """
        Delete comment in Linear
        
        Args:
            external_id: Linear comment ID
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"[Linear] Deleting comment: {external_id}")
            result = await self._client.delete_comment(external_id)
            
            if result.get('success', False):
                logger.info(f"✓ Deleted Linear comment: {external_id}")
                return True
            else:
                logger.warning(f"Failed to delete Linear comment: {external_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete Linear comment: {str(e)}")
            raise
    