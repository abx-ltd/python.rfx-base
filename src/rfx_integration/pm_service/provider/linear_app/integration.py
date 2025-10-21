import httpx
from typing import Dict, Any, Optional
from fluvius.data import logger

from . import config


class LinearIntegration:
    """Linear API Integration Client via UAPI using httpx"""
    
    def __init__(self):
        self.api_key = config.LINEAR_API_KEY
        self.team_id = config.LINEAR_TEAM_ID
        self.uapi_url = config.UAPI_URL
        self.connection_id = config.LINEAR_CONNECTION_ID
        self._client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx async client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self):
        """Close httpx client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _call_linear_api(self, graphql_query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Linear API through UAPI proxy using httpx
        
        Args:
            graphql_query: GraphQL query/mutation string
            variables: GraphQL variables
            
        Returns:
            Response data from Linear API
        """
        payload = {
            "query": graphql_query,
            "variables": variables
        }
        
        uapi_payload = {
            "connection_id": self.connection_id,
            "action": "call-api",
            "payload": payload
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            client = await self._get_client()
            response = await client.post(
                self.uapi_url,
                headers=headers,
                json=uapi_payload
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[Linear UAPI] Response: {result}")
            
            # Extract data from UAPI response structure
            # UAPI returns: {"result": {"data": {...}, "errors": [...]}}
            result_data = result.get('result', {})
            
            # Check for GraphQL errors
            if "errors" in result_data:
                logger.error(f"Linear GraphQL Error: {result_data['errors']}")
                raise Exception(f"Linear API Error: {result_data['errors']}")
            
            return result_data.get('data', {})
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to call Linear API via UAPI: {str(e)}")
            raise Exception(f"UAPI request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Linear API: {str(e)}")
            raise
    
    # ---------- Issue Operations ----------
    
    async def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new issue in Linear
        
        Args:
            issue_data: {
                "id": str (optional - your internal ID),
                "title": str,
                "description": str,
                "teamId": str,
                "projectId": str (optional),
                "priority": int (1-4),
                "estimate": int (optional),
                "assigneeId": str (optional),
                "stateId": str (optional),
                "labelIds": list (optional),
                "parentId": str (optional)
            }
        """
        from .gql_queries import CREATE_ISSUE_MUTATION
        
        # Ensure teamId is set
        if "teamId" not in issue_data:
            issue_data["teamId"] = self.team_id
        
        variables = {"input": issue_data}
        
        result = await self._call_linear_api(CREATE_ISSUE_MUTATION, variables)
        
        issue = result.get('issueCreate', {}).get('issue', {})
        
        if not issue:
            raise Exception("Failed to create issue in Linear")
        
        logger.info(f"Created Linear issue: {issue.get('identifier')} (ID: {issue.get('id')})")
        return issue
    
    async def update_issue(self, issue_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing issue in Linear
        
        Args:
            issue_id: Linear issue ID (UUID)
            data: Update fields (title, description, priority, etc.)
        """
        from .gql_queries import UPDATE_ISSUE_MUTATION
        
        variables = {
            "issueId": issue_id,
            "input": data
        }
        
        result = await self._call_linear_api(UPDATE_ISSUE_MUTATION, variables)
        
        update_result = result.get('issueUpdate', {})
        
        if not update_result.get('success'):
            raise Exception(f"Failed to update Linear issue {issue_id}")
        
        logger.info(f"Updated Linear issue: {issue_id}")
        return update_result
    
    async def delete_issue(self, issue_id: str, permanently: bool = True) -> Dict[str, Any]:
        """
        Delete (permanently) or archive an issue in Linear
        
        Args:
            issue_id: Linear issue ID
            permanently: If True, permanently delete. If False, archive.
        """
        from .gql_queries import DELETE_ISSUE_MUTATION
        
        variables = {
            "issueDeleteId": issue_id,
            "permanentlyDelete": permanently
        }
        
        result = await self._call_linear_api(DELETE_ISSUE_MUTATION, variables)
        
        delete_result = result.get('issueDelete', {})
        
        if not delete_result.get('success'):
            raise Exception(f"Failed to delete Linear issue {issue_id}")
        
        logger.info(f"Deleted Linear issue: {issue_id}")
        return delete_result
    
    async def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Get issue details from Linear"""
        from .gql_queries import CHECK_ISSUE_EXISTS_QUERY
        
        variables = {"issueId": issue_id}
        
        result = await self._call_linear_api(CHECK_ISSUE_EXISTS_QUERY, variables)
        
        issue = result.get('issue')
        
        if not issue:
            raise Exception(f"Issue {issue_id} not found in Linear")
        
        return issue
    
    async def check_issue_exists(self, issue_id: str) -> Dict[str, Any]:
        """Check if issue exists in Linear"""
        try:
            issue = await self.get_issue(issue_id)
            return {
                "exists": True,
                "message": "Issue còn hoạt động bình thường.",
                "data": issue
            }
        except Exception as e:
            logger.warning(f"[Linear] Issue {issue_id} not found: {str(e)}")
            return {
                "exists": False,
                "message": "Không tìm thấy issue trên Linear."
            }
    
    # ---------- Comment Operations ----------
    
    async def create_comment(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comment in Linear
        
        Args:
            comment_data: {
                "id": str (optional - your internal ID),
                "body": str,
                "issueId": str,
                "parentId": str (optional - for nested comments)
            }
        """
        from .gql_queries import CREATE_ISSUE_MUTATION_COMMENT
        
        variables = {"input": comment_data}
        
        result = await self._call_linear_api(CREATE_ISSUE_MUTATION_COMMENT, variables)
        
        comment = result.get('commentCreate', {}).get('comment', {})
        
        if not comment:
            raise Exception("Failed to create comment in Linear")
        
        logger.info(f"Created Linear comment: {comment.get('id')}")
        return comment
    
    async def update_comment(self, comment_id: str, body: str) -> Dict[str, Any]:
        """Update comment in Linear"""
        from .gql_queries import UPDATE_ISSUE_MUTATION_COMMENT
        
        variables = {
            "commentUpdateId": comment_id,
            "input": {"body": body}
        }
        
        result = await self._call_linear_api(UPDATE_ISSUE_MUTATION_COMMENT, variables)
        
        update_result = result.get('commentUpdate', {})
        
        if not update_result.get('success'):
            raise Exception(f"Failed to update Linear comment {comment_id}")
        
        logger.info(f"Updated Linear comment: {comment_id}")
        return update_result
    
    async def delete_comment(self, comment_id: str) -> Dict[str, Any]:
        """Delete comment in Linear"""
        from .gql_queries import DELETE_ISSUE_MUTATION_COMMENT
        
        variables = {"commentDeleteId": comment_id}
        
        result = await self._call_linear_api(DELETE_ISSUE_MUTATION_COMMENT, variables)
        
        delete_result = result.get('commentDelete', {})
        
        if not delete_result.get('success'):
            raise Exception(f"Failed to delete Linear comment {comment_id}")
        
        logger.info(f"Deleted Linear comment: {comment_id}")
        return delete_result
    
    async def get_comment(self, comment_id: str) -> Dict[str, Any]:
        """Get comment details from Linear"""
        from .gql_queries import CHECK_COMMENT_EXISTS_QUERY
        
        variables = {"id": comment_id}
        
        result = await self._call_linear_api(CHECK_COMMENT_EXISTS_QUERY, variables)
        
        comment = result.get('comment')
        
        if not comment:
            raise Exception(f"Comment {comment_id} not found in Linear")
        
        return comment
    
    async def check_comment_exists(self, comment_id: str) -> Dict[str, Any]:
        """Check if comment exists in Linear"""
        try:
            comment = await self.get_comment(comment_id)
            return {
                "exists": True,
                "message": "Comment còn hoạt động bình thường.",
                "data": comment
            }
        except Exception as e:
            logger.warning(f"[Linear] Comment {comment_id} not found: {str(e)}")
            return {
                "exists": False,
                "message": "Không tìm thấy comment trên Linear."
            }


# Helper functions for mapping
def get_linear_status_id(status_name: str) -> Optional[str]:
    """Map internal status to Linear state ID"""
    status_map = {
        "DRAFT": "a291583a-c46a-4096-9df7-ad9046cd39fd",         
        "ACTIVE": "a291583a-c46a-4096-9df7-ad9046cd39fd",      
        "IN_PROGRESS": "022d6dca-d63c-4ee0-9768-40a3c2d99592",
        "PLANNED": "2d517b0e-9395-40ba-a1fa-e1986ee76c7c",      
        "COMPLETED": "3f192138-2d5e-4cc1-97ee-08bd54df6130",   
        "CANCELED": "c4d86fca-29ca-48b1-8a2c-168a7f954d23"     
    }
    return status_map.get(status_name.upper())


def get_linear_user_id(creator_id: str) -> Optional[str]:
    """Map internal user ID to Linear user ID"""
    user_map = {
        "e28bdf52-53fa-412e-87ad-d830f94a7984": "b8g3vffu-ehi5-hdu-e4si-n05uuk-gc7-pnoc"
    }
    return user_map.get(creator_id)


def get_linear_label_id(category_name: str) -> Optional[str]:
    """Map internal category to Linear label ID"""
    label_map = {
        "ARCHITECTURE": "c78c123d-4c44-5d5e-6a62-78d1ef73c71d"
    }
    return label_map.get(category_name.upper())


def map_priority(priority_value: str) -> int:
    """Map priority string to Linear priority number (1-4)"""
    priority_map = {
        "URGENT": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4,
        "NO_PRIORITY": 0
    }
    return priority_map.get(priority_value.upper(), 3)