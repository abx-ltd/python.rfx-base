from fluvius.data import logger
from . import gql_queries
from .integration import call_linear_api, get_linear_status_id, get_linear_user_id, get_linear_label_id
from .utils import safe_getattr, map_priority, parse_date
from fluvius.data import logger
from . import config

class LinearService:
    """Service layer for interacting with Linear GraphQL API."""

    TEAM_ID = config.DEFAULT_TEAM_ID

    # ---------- Issue ----------
    @classmethod
    def create_issue(cls, ticket, project_id, ticket_id):
        issue_id = str(ticket_id)
        title = ticket.get("title", "New Issue") 
        description = ticket.get("description")
        

        priority_value = ticket.get("priority", "MEDIUM")
        priority = map_priority(priority_value)

        assignee_id = ticket.get("assignee")  # Dùng key 'assignee' như trong log
        parent_id = ticket.get("parent_id")   # key này không có nên sẽ trả về None
        #due_date = parse_date(safe_getattr(ticket, "due_date"))
        logger.info(f"ticket data: {ticket}")
        logger.info(f"assignee_id: {assignee_id}")
        logger.info(f"parent_id: {parent_id}")
        logger.info(f"priority: {priority}")
        logger.info(f"title: {title}")
        logger.info(f"description: {description}")
        logger.info(f"issue_id: {issue_id}")
        logger.info(f"project_id: {project_id}")
        
        gql_payload = {
            "query": gql_queries.CREATE_ISSUE_MUTATION,
            "variables": {
                "input": {
                    "id": str(issue_id),
                    "title": title,
                    "description": description,
                    "priority": 3,
                    "estimate": 5,
                    #"assigneeId": str(assignee_id) if assignee_id else None,
                    "teamId": cls.TEAM_ID,
                    "projectId": str(project_id)
                }
            },
        }
        return call_linear_api(payload=gql_payload)
    
    
    @classmethod
    def update_issue(cls, ticket, ticket_id):
        issue_id = str(ticket_id)
        title = ticket.get("title")
        description = ticket.get("description")
        priority_value = ticket.get("priority", "MEDIUM")
        priority = map_priority(priority_value)
        assignee_id = ticket.get("assignee")
        parent_id = ticket.get("parent_id")
        #due_date = parse_date(safe_getattr(ticket, "due_date"))

        logger.info(f"[Linear] Updating issue {issue_id} (title={title}, priority={priority_value})")

        gql_payload = {
            "query": gql_queries.UPDATE_ISSUE_MUTATION,
            "variables": {
                "issueId": str(issue_id),
                "input": {
                    "title": title,
                    "description": description,
                    "priority": priority,
                    #"assigneeId": str(assignee_id) if assignee_id else None,
                    #"parentId": str(parent_id) if parent_id else None,
                }
            },
        }
        return call_linear_api(payload=gql_payload)
    
    
    @classmethod
    def delete_issue(cls, ticket_id):
        issue_id = str(ticket_id)
        gql_payload = {
            "query": gql_queries.DELETE_ISSUE_MUTATION,
            "variables": {
                "issueDeleteId": issue_id,
                "permanentlyDelete": True
            }
        }
        return call_linear_api(payload=gql_payload)
    @classmethod
    def check_issue_exists(cls, issue_id):
        gql_payload = {
            "query": gql_queries.CHECK_ISSUE_EXISTS_QUERY,
            "variables": {"issueId": str(issue_id)},            
        }   

        result = call_linear_api(payload=gql_payload)
        logger.info(f"[Linear] Raw check issue response: {result}")

        issue_data = (
            result.get("result", {})
                  .get("data", {})
                  .get("issue")
        )

        if not issue_data:
            logger.warning(f"[Linear] Issue {issue_id} not found on Linear")
            return {"exists": False, "message": "Không tìm thấy issue trên Linear."}

        return {"exists": True, "message": "Issue còn hoạt động bình thường."}

    #---------- Linear Service for Comment--------
    @classmethod
    def create_comment(cls, comment, issue_id):
        """Create comment in Linear"""
        comment_id = str(comment.get("_id"))
        body = comment.get("content", "")
        parent_comment_id = comment.get("parent_id")
        
        logger.info(f"[Linear] Creating comment for issue {issue_id}")
        logger.info(f"comment data: {comment}")
        logger.info(f"comment_id: {comment_id}")
        logger.info(f"body: {body}")
        logger.info(f"parent_comment_id: {parent_comment_id}")
        
        input_data = {
            "id": comment_id,
            "body": body,
            "issueId": str(issue_id)
        }
        
        if parent_comment_id not in [None, ""]:
            input_data["parentId"] = str(parent_comment_id)
        
        gql_payload = {
            "query": gql_queries.CREATE_ISSUE_MUTATION_COMMENT,
            "variables": {
                "input": input_data
            },
        }
        
        return call_linear_api(payload=gql_payload)
    
    @classmethod
    def update_comment(cls, comment, comment_id):
        """Update comment in Linear"""
        body = comment.get("content", "")
        
        logger.info(f"[Linear] Updating comment {comment_id}")
        
        gql_payload = {
            "query": gql_queries.UPDATE_ISSUE_MUTATION_COMMENT,
            "variables": {
                "commentUpdateId": str(comment_id),
                "input": {
                    "body": body
                }
            },
        }
        
        return call_linear_api(payload=gql_payload)
    
    @classmethod
    def delete_comment(cls, comment_id):
        """Delete comment in Linear"""
        logger.info(f"[Linear] Deleting comment {comment_id}")
        
        gql_payload = {
            "query": gql_queries.DELETE_ISSUE_MUTATION_COMMENT,
            "variables": {
                "commentDeleteId": str(comment_id)
            }
        }
        
        return call_linear_api(payload=gql_payload)
    
    @classmethod
    def check_comment_exists(cls, comment_id):
        """Check if comment exists in Linear"""
        gql_payload = {
            "query": gql_queries.CHECK_COMMENT_EXISTS_QUERY,
            "variables": {"id": str(comment_id)},            
        }   

        result = call_linear_api(payload=gql_payload)
        logger.info(f"[Linear] Raw check comment response: {result}")

        comment_data = (
            result.get("result", {})
                  .get("data", {})
                  .get("comment")
        )

        if not comment_data:
            logger.warning(f"[Linear] Comment {comment_id} not found on Linear")
            return {"exists": False, "message": "Không tìm thấy comment trên Linear."}

        return {"exists": True, "message": "Comment còn hoạt động bình thường."}

        