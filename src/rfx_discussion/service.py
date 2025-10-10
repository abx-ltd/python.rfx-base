from fluvius.data import logger
from . import gql_queries
from .integration import call_linear_api, get_linear_status_id, get_linear_user_id, get_linear_label_id
from .utils import safe_getattr, map_priority, parse_date
from fluvius.data import logger

class LinearService:
    """Service layer for interacting with Linear GraphQL API."""

    TEAM_ID = "a7fc113d-5b51-4f6e-8a82-18eccf73c71c"

    @staticmethod
    def create_issue(issue):
        title = safe_getattr(issue, "title")
        description = safe_getattr(issue, "description")
        priority = map_priority(safe_getattr(issue, "priority", "MEDIUM"))
        assignee_id = get_linear_user_id(safe_getattr(issue, "assignee"))
        parent_id = safe_getattr(issue, "parent_id")

        input_data = {
            # DO NOT send local id on create; Linear generates it
            "teamId": LinearService.TEAM_ID,
            "title": title,
            "description": description,
            "priority": priority,
            "assigneeId": assignee_id,
            "parentId": str(parent_id) if parent_id else None,
        }
        # Strip None values to avoid serialization of enums/None
        input_data = {k: v for k, v in input_data.items() if v is not None}

        gql_payload = {
            "query": gql_queries.CREATE_ISSUE_MUTATION,
            "variables": {"input": input_data},
        }

        return call_linear_api(payload=gql_payload)

    @staticmethod
    def update_issue(issue):
        # Map/convert fields to JSON-serializable and Linear-acceptable values
        input_data = {
            "id": str(safe_getattr(issue, "_id")),
            "title": safe_getattr(issue, "title"),
            "description": safe_getattr(issue, "description"),
            "priority": map_priority(safe_getattr(issue, "priority", "MEDIUM")),
            "assigneeId": get_linear_user_id(safe_getattr(issue, "assignee")),
            "parentId": str(safe_getattr(issue, "parent_id")) if safe_getattr(issue, "parent_id") else None,
        }
        input_data = {k: v for k, v in input_data.items() if v is not None}

        gql_payload = {
            "query": gql_queries.UPDATE_ISSUE_MUTATION,
            "variables": {"input": input_data},
        }
        return call_linear_api(payload=gql_payload)
    
    @staticmethod
    def delete_issue(issue):
        gql_payload = {
            "query": gql_queries.DELETE_ISSUE_MUTATION,
            "variables": {
                "input": {
                    "id": str(issue._id)
                    }
                }
        }
        return call_linear_api(payload=gql_payload)


    @staticmethod
    def check_issue_exists(issue_id):
        gql_payload = {
            "query": gql_queries.CHECK_ISSUE_EXISTS_QUERY,
            "variables": {
                "issueId": str(issue_id)
                },
        }

        result = call_linear_api(payload=gql_payload)
        logger.info(f"[Linear] Raw check response: {result}")


        issue_data = (
            result.get("result", {})
                  .get("data", {})
                  .get("issue")
        )

        if not issue_data:
            logger.warning(f"[Linear] Issue {issue_id} not found on Linear")
            return {"exists": False, "message": "Không tìm thấy issue trên Linear."}

        if issue_data.get("deletedAt") or issue_data.get("trashed"):
            msg = f"Issue {issue_data.get('title')} đã bị xoá trên Linear."
            logger.warning(f"[Linear] {msg}")
            return {"exists": False, "message": msg}

        if issue_data.get("archivedAt"):
            msg = f"Issue {issue_data.get('title')} đã bị lưu trữ (archived)."
            logger.warning(f"[Linear] {msg}")
            return {"exists": False, "message": msg}

        return {"exists": True, "message": "Issue còn hoạt động bình thường."}