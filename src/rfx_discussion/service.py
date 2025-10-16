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

    # @staticmethod
    # def create_issue(issue):
    #     title = safe_getattr(issue, "title")
    #     description = safe_getattr(issue, "description")
    #     priority = map_priority(safe_getattr(issue, "priority", "MEDIUM"))
    #     assignee_id = get_linear_user_id(safe_getattr(issue, "assignee"))
    #     parent_id = safe_getattr(issue, "parent_id")

    #     input_data = {
    #         # DO NOT send local id on create; Linear generates it
    #         "teamId": LinearService.TEAM_ID,
    #         "title": title,
    #         "description": description,
    #         "priority": priority,
    #         "assigneeId": assignee_id,
    #         "parentId": str(parent_id) if parent_id else None,
    #     }
    #     # Strip None values to avoid serialization of enums/None
    #     input_data = {k: v for k, v in input_data.items() if v is not None}

    #     gql_payload = {
    #         "query": gql_queries.CREATE_ISSUE_MUTATION,
    #         "variables": {"input": input_data},
    #     }

    #     return call_linear_api(payload=gql_payload)

    # @staticmethod
    # def update_issue(issue):
    #     # Map/convert fields to JSON-serializable and Linear-acceptable values
    #     input_data = {
    #         "id": str(safe_getattr(issue, "_id")),
    #         "title": safe_getattr(issue, "title"),
    #         "description": safe_getattr(issue, "description"),
    #         "priority": map_priority(safe_getattr(issue, "priority", "MEDIUM")),
    #         "assigneeId": get_linear_user_id(safe_getattr(issue, "assignee")),
    #         "parentId": str(safe_getattr(issue, "parent_id")) if safe_getattr(issue, "parent_id") else None,
    #     }
    #     input_data = {k: v for k, v in input_data.items() if v is not None}

    #     gql_payload = {
    #         "query": gql_queries.UPDATE_ISSUE_MUTATION,
    #         "variables": {"input": input_data},
    #     }
    #     return call_linear_api(payload=gql_payload)
    
    # @staticmethod
    # def delete_issue(issue):
    #     gql_payload = {
    #         "query": gql_queries.DELETE_ISSUE_MUTATION,
    #         "variables": {
    #             "input": {
    #                 "id": str(issue._id)
    #                 }
    #             }
    #     }
    #     return call_linear_api(payload=gql_payload)


    # @staticmethod
    # def check_issue_exists(issue_id):
    #     gql_payload = {
    #         "query": gql_queries.CHECK_ISSUE_EXISTS_QUERY,
    #         "variables": {
    #             "issueId": str(issue_id)
    #             },
    #     }

    #     result = call_linear_api(payload=gql_payload)
    #     logger.info(f"[Linear] Raw check response: {result}")


    #     issue_data = (
    #         result.get("result", {})
    #               .get("data", {})
    #               .get("issue")
    #     )

    #     if not issue_data:
    #         logger.warning(f"[Linear] Issue {issue_id} not found on Linear")
    #         return {"exists": False, "message": "Không tìm thấy issue trên Linear."}

    #     if issue_data.get("deletedAt") or issue_data.get("trashed"):
    #         msg = f"Issue {issue_data.get('title')} đã bị xoá trên Linear."
    #         logger.warning(f"[Linear] {msg}")
    #         return {"exists": False, "message": msg}

    #     if issue_data.get("archivedAt"):
    #         msg = f"Issue {issue_data.get('title')} đã bị lưu trữ (archived)."
    #         logger.warning(f"[Linear] {msg}")
    #         return {"exists": False, "message": msg}

    #     return {"exists": True, "message": "Issue còn hoạt động bình thường."}