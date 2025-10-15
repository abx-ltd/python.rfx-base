from fluvius.data import logger
from . import gql_queries
from .integration import call_linear_api, get_linear_status_id, get_linear_user_id, get_linear_label_id
from .utils import safe_getattr, map_priority, parse_date
from . import config

class LinearService:
    """Service layer for interacting with Linear GraphQL API."""

    TEAM_ID = config.DEFAULT_TEAM_ID

    # ---------- Create ----------
    @classmethod
    def create_project(cls, project):

        logger.info(f"[Linear] Creating project: {project}")
        project_id = safe_getattr(project, "_id")
        name = safe_getattr(project, "name", "New Project")
        description = safe_getattr(project, "description")
        start_date = parse_date(safe_getattr(project, "start_date"))
        target_date = parse_date(safe_getattr(project, "target_date"))
        priority = map_priority(safe_getattr(project, "priority", "MEDIUM"))
        status = safe_getattr(project, "status", "DRAFT")

        gql_payload = {
            "query": gql_queries.CREATE_PROJECT_MUTATION,
            "variables": {
                "input": {
                    "id": str(project_id),
                    "name": name,
                    "description": description,
                    "startDate": start_date,
                    "targetDate": target_date,
                    "priority": priority,
                    "statusId": get_linear_status_id(status),
                    "teamIds": [cls.TEAM_ID],
                }
            },
        }

        return call_linear_api(payload=gql_payload)

    # ---------- Update ----------
    @classmethod
    def update_project(cls, project):
        project_id = safe_getattr(project, "_id")
        name = safe_getattr(project, "name")
        description = safe_getattr(project, "description")
        start_date = parse_date(safe_getattr(project, "start_date"))
        target_date = parse_date(safe_getattr(project, "target_date"))
        priority = map_priority(safe_getattr(project, "priority", "MEDIUM"))
        status = safe_getattr(project, "status")

        logger.info(f"[Linear] Updating project {project_id} (status={status})")

        gql_payload = {
            "query": gql_queries.UPDATE_PROJECT_MUTATION,
            "variables": {
                "id": str(project_id),
                "input": {
                    "name": name,
                    "description": description,
                    "startDate": start_date,
                    "targetDate": target_date,
                    "priority": priority,
                    "statusId": get_linear_status_id(status),
                },
            },
        }

        return call_linear_api(payload=gql_payload)

    # ---------- Delete ----------
    @classmethod
    def delete_project(cls, project_id):
        gql_payload = {
            "query": gql_queries.DELETE_PROJECT_MUTATION,
            "variables": {"projectDeleteId": str(project_id)},
        }
        return call_linear_api(payload=gql_payload)

    # ---------- Check existence ----------
    @classmethod
    def check_project_exists(cls, project_id):
        gql_payload = {
            "query": gql_queries.CHECK_PROJECT_EXISTS_QUERY,
            "variables": {"projectId": str(project_id)},
        }

        result = call_linear_api(payload=gql_payload)
        logger.info(f"[Linear] Raw check response: {result}")

        project_data = (
            result.get("result", {})
                  .get("data", {})
                  .get("project")
        )

        if not project_data:
            logger.warning(f"[Linear] Project {project_id} not found on Linear")
            return {"exists": False, "message": "Không tìm thấy project trên Linear."}

        if project_data.get("deletedAt") or project_data.get("trashed"):
            msg = f"Project {project_data.get('name')} đã bị xoá trên Linear."
            logger.warning(f"[Linear] {msg}")
            return {"exists": False, "message": msg}

        if project_data.get("archivedAt"):
            msg = f"Project {project_data.get('name')} đã bị lưu trữ (archived)."
            logger.warning(f"[Linear] {msg}")
            return {"exists": False, "message": msg}

        return {"exists": True, "message": "Project còn hoạt động bình thường."}
    
    @classmethod
    def get_project_url(cls, project_id):
        gql_payload = {
            "query": gql_queries.GET_PROJECTS_QUERY_URL,
            "variables": {"projectId": str(project_id)},
        }
        logger.info(f"[Linear] Checking URL for project ID: {project_id}")
        result = call_linear_api(payload=gql_payload)
        logger.info(f"[Linear] Raw check response: {result}")
        project_data = result.get("result", {}).get("data", {}).get("project", {})
        url = project_data.get("url")
        if not url:
            raise ValueError(f"Không thể tìm thấy URL cho project với ID: {project_id}")
        return url

    # Milestone
    @classmethod
    def create_milestone(cls, milestone):
        
        milestone_id = safe_getattr(milestone, "_id")
        project_id = safe_getattr(milestone, "project_id")
        
        logger.info(f"[Linear] Creating milestone {milestone_id} for project {project_id}")
        
        name = safe_getattr(milestone, "name", "New Milestone")
        description = safe_getattr(milestone, "description")
        target_date = parse_date(safe_getattr(milestone, "due_date"))
        sort_order = 1.0

        gql_payload = {
            "query": gql_queries.CREATE_PROJECT_MILESTONE_MUTATION,
            "variables": {
                "input": {
                    "id": str(milestone_id),
                    "name": name,
                    "description": description,
                    "projectId": str(project_id),
                    "targetDate": target_date,
                    "sortOrder": sort_order 
                }
            },
        }
        return call_linear_api(payload=gql_payload)
    
    @classmethod
    def update_milestone(cls, milestone):
        
        milestone_id = safe_getattr(milestone, "_id")
        logger.info(f"[Linear] Updating milestone {milestone_id}")
        name = safe_getattr(milestone, "name")
        description = safe_getattr(milestone, "description")
        target_date = parse_date(safe_getattr(milestone, "due_date"))

        logger.info(f"[Linear] Updating milestone {milestone_id}")

        gql_payload = {
            "query": gql_queries.UPDATE_PROJECT_MILESTONE_MUTATION,
            "variables": {
                "projectMilestoneUpdateId": str(milestone_id),
                "input": {
                    "name": name,
                    "description": description,
                    "targetDate": target_date,
                },
            },
        }
        return call_linear_api(payload=gql_payload)
    
    @classmethod
    def delete_milestone(cls, milestone_id):
        
        logger.info(f"[Linear] Deleting milestone {milestone_id}")
        gql_payload = {
            "query": gql_queries.DELETE_PROJECT_MILESTONE_MUTATION,
            "variables": {
                "projectMilestoneDeleteId": str(milestone_id)
            },
        }
        return call_linear_api(payload=gql_payload)
    
        
    @classmethod
    def check_milestone_exists(cls, milestone_id):
        gql_payload = {
            "query": gql_queries.CHECK_PROJECT_MILESTONE_EXISTS_QUERY,
            "variables": {"projectMilestoneId": str(milestone_id)},
        }

        result = call_linear_api(payload=gql_payload)
        logger.info(f"[Linear] Raw check milestone response: {result}")

        milestone_data = (
            result.get("result", {})
                  .get("data", {})
                  .get("projectMilestone")
        )
        logger.info(f"[Linear] Parsed milestone data: {milestone_data}")

        if not milestone_data:
            logger.warning(f"[Linear] Milestone {milestone_id} not found on Linear")
            return {"exists": False, "message": "Không tìm thấy milestone trên Linear."}

        if milestone_data.get("deletedAt") or milestone_data.get("trashed"):
            msg = f"Milestone {milestone_data.get('name')} đã bị xoá trên Linear."
            logger.warning(f"[Linear] {msg}")
            return {"exists": False, "message": msg}

        if milestone_data.get("archivedAt"):
            msg = f"Milestone {milestone_data.get('name')} đã bị lưu trữ (archived)."
            logger.warning(f"[Linear] {msg}")
            return {"exists": False, "message": msg}

        return {"exists": True, "message": "Milestone còn hoạt động bình thường."}
        
    
