from ..base import (
    PMService, 
    CreateTicketPayload, 
    CreateTicketResponse, 
    UpdateTicketPayload, 
    UpdateTicketResponse
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
    
    # ---------- Comment Operations ----------
    
    async def create_comment(
        self, 
        issue_id: str, 
        content: str, 
        comment_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create comment in Linear
        
        Args:
            issue_id: Linear issue ID (external_id)
            content: Comment body/content
            comment_id: Your internal comment ID (optional)
            parent_id: Parent comment ID for nested comments (optional)
        """
        comment_data = {
            "body": content,
            "issueId": issue_id
        }
        
        if comment_id:
            comment_data["id"] = str(comment_id)
        
        if parent_id:
            comment_data["parentId"] = str(parent_id)
        
        try:
            logger.info(f"[Linear] Creating comment for issue {issue_id}")
            return await self._client.create_comment(comment_data)
        except Exception as e:
            logger.error(f"Failed to create Linear comment: {str(e)}")
            raise
    
    async def update_comment(self, comment_id: str, content: str) -> Dict[str, Any]:
        """Update comment in Linear"""
        try:
            logger.info(f"[Linear] Updating comment {comment_id}")
            return await self._client.update_comment(comment_id, content)
        except Exception as e:
            logger.error(f"Failed to update Linear comment: {str(e)}")
            raise
    
    async def delete_comment(self, comment_id: str) -> bool:
        """Delete comment in Linear"""
        try:
            result = await self._client.delete_comment(comment_id)
            return result.get('success', False)
        except Exception as e:
            logger.error(f"Failed to delete Linear comment: {str(e)}")
            return False
    
    async def check_comment_exists(self, comment_id: str) -> Dict[str, Any]:
        """Check if comment exists in Linear"""
        return await self._client.check_comment_exists(comment_id)