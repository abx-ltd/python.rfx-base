import httpx
from typing import Dict, Any, Optional
from fluvius.data import logger

from . import config
from .gql_queries import (
    CREATE_ISSUE_MUTATION,
    UPDATE_ISSUE_MUTATION,
    DELETE_ISSUE_MUTATION,
    CREATE_ISSUE_MUTATION_COMMENT,
    UPDATE_ISSUE_MUTATION_COMMENT,
    DELETE_ISSUE_MUTATION_COMMENT,
    CHECK_COMMENT_EXISTS_QUERY,
    CREATE_PROJECT_MUTATION,
    UPDATE_PROJECT_MUTATION,
    DELETE_PROJECT_MUTATION,
    ARCHIVE_PROJECT_MUTATION,
    CHECK_PROJECT_EXISTS_QUERY,
    CREATE_PROJECT_MILESTONE_MUTATION,
    UPDATE_PROJECT_MILESTONE_MUTATION,
    DELETE_PROJECT_MILESTONE_MUTATION,
    GET_PROJECT_MILESTONE_QUERY,
    LIST_PROJECT_MILESTONES_QUERY,
    CREATE_PROJECT_UPDATE_MUTATION,
    GET_PROJECT_UPDATE_QUERY,
    LIST_PROJECT_UPDATES_QUERY,
)


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

    async def _call_linear_api(
        self, graphql_query: str, variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        payload = {"query": graphql_query, "variables": variables}

        uapi_payload = {
            "connection_id": self.connection_id,
            "action": "call-api",
            "payload": payload,
        }

        headers = {"Content-Type": "application/json"}

        try:
            client = await self._get_client()
            response = await client.post(
                self.uapi_url, headers=headers, json=uapi_payload
            )
            response.raise_for_status()
            result = response.json()

            result_data = result.get("result", {})

            if "errors" in result_data:
                logger.error(f"Linear GraphQL Error: {result_data['errors']}")
                raise Exception(f"Linear API Error: {result_data['errors']}")

            return result_data.get("data", {})

        except httpx.HTTPError as e:
            logger.error(f"Failed to call Linear API via UAPI: {str(e)}")
            raise Exception(f"UAPI request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Linear API: {str(e)}")
            raise

    # ---------- Issue Operations ----------

    async def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure teamId is set
        if "teamId" not in issue_data:
            issue_data["teamId"] = self.team_id

        variables = {"input": issue_data}

        result = await self._call_linear_api(CREATE_ISSUE_MUTATION, variables)

        issue = result.get("issueCreate", {}).get("issue", {})

        if not issue:
            raise Exception("Failed to create issue in Linear")
        return issue

    async def update_issue(self, issue_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        variables = {"issueId": issue_id, "input": data}

        result = await self._call_linear_api(UPDATE_ISSUE_MUTATION, variables)

        update_result = result.get("issueUpdate", {})

        if not update_result.get("success"):
            raise Exception(f"Failed to update Linear issue {issue_id}")
        return update_result

    async def delete_issue(
        self, issue_id: str, permanently: bool = True
    ) -> Dict[str, Any]:
        variables = {"issueDeleteId": issue_id, "permanentlyDelete": permanently}

        result = await self._call_linear_api(DELETE_ISSUE_MUTATION, variables)

        delete_result = result.get("issueDelete", {})

        if not delete_result.get("success"):
            raise Exception(f"Failed to delete Linear issue {issue_id}")

        return delete_result

    async def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Get issue details from Linear"""
        from .gql_queries import CHECK_ISSUE_EXISTS_QUERY

        variables = {"issueId": issue_id}

        result = await self._call_linear_api(CHECK_ISSUE_EXISTS_QUERY, variables)

        issue = result.get("issue")

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
                "data": issue,
            }
        except Exception as e:
            logger.warning(f"[Linear] Issue {issue_id} not found: {str(e)}")
            return {"exists": False, "message": "Không tìm thấy issue trên Linear."}

    # ---------- Comment Operations ----------

    async def create_comment(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        variables = {"input": comment_data}

        result = await self._call_linear_api(CREATE_ISSUE_MUTATION_COMMENT, variables)

        comment = result.get("commentCreate", {}).get("comment", {})

        if not comment:
            raise Exception("Failed to create comment in Linear")

        return comment

    async def update_comment(self, comment_id: str, body: str) -> Dict[str, Any]:
        """Update comment in Linear"""

        variables = {"commentUpdateId": comment_id, "input": {"body": body}}

        result = await self._call_linear_api(UPDATE_ISSUE_MUTATION_COMMENT, variables)

        update_result = result.get("commentUpdate", {})

        if not update_result.get("success"):
            raise Exception(f"Failed to update Linear comment {comment_id}")

        logger.info(f"Updated Linear comment: {comment_id}")
        return update_result

    async def delete_comment(self, external_id: str) -> Dict[str, Any]:
        """Delete comment in Linear"""

        variables = {"commentDeleteId": external_id}

        result = await self._call_linear_api(DELETE_ISSUE_MUTATION_COMMENT, variables)

        delete_result = result.get("commentDelete", {})

        if not delete_result.get("success"):
            raise Exception(f"Failed to delete Linear comment {external_id}")

        return delete_result

    async def get_comment(self, comment_id: str) -> Dict[str, Any]:
        """Get comment details from Linear"""

        variables = {"id": comment_id}

        result = await self._call_linear_api(CHECK_COMMENT_EXISTS_QUERY, variables)

        comment = result.get("comment")

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
                "data": comment,
            }
        except Exception as e:
            logger.warning(f"[Linear] Comment {comment_id} not found: {str(e)}")
            return {"exists": False, "message": "Không tìm thấy comment trên Linear."}

    # ---------- Project Operations ----------
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        # Validate required fields
        if "name" not in project_data:
            raise ValueError("Project name is required")

        if "teamIds" not in project_data or not project_data["teamIds"]:
            # Use default team if not specified
            project_data["teamIds"] = [self.team_id]

        variables = {"input": project_data}
        result = await self._call_linear_api(CREATE_PROJECT_MUTATION, variables)

        project = result.get("projectCreate", {}).get("project", {})
        if not project:
            raise Exception("Failed to create project in Linear")

        return project

    async def update_project(
        self, project_id: str, project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        cleaned_data = {}

        if project_data.get("name"):
            cleaned_data["name"] = str(project_data["name"])

        if project_data.get("description"):
            cleaned_data["description"] = str(project_data["description"])

        if project_data.get("leadId"):
            cleaned_data["leadId"] = str(project_data["leadId"])

        if project_data.get("state"):
            # Validate state
            valid_states = ["planned", "started", "paused", "completed", "canceled"]
            if project_data["state"] in valid_states:
                cleaned_data["state"] = project_data["state"]

        if project_data.get("color"):
            cleaned_data["color"] = str(project_data["color"])

        if project_data.get("icon"):
            cleaned_data["icon"] = str(project_data["icon"])

        if project_data.get("startDate"):
            cleaned_data["startDate"] = project_data["startDate"]

        if project_data.get("targetDate"):
            cleaned_data["targetDate"] = project_data["targetDate"]

        if not cleaned_data:
            logger.warning(f"No valid fields to update for project {project_id}")
            return {"id": project_id}

        variables = {
            "id": str(project_id),
            "input": cleaned_data,
        }

        result = await self._call_linear_api(UPDATE_PROJECT_MUTATION, variables)

        project = result.get("projectUpdate", {}).get("project", {})
        if not project:
            raise Exception(f"Failed to update project {project_id} in Linear")

        return project

    async def delete_project(
        self, project_id: str, permanently: bool = False
    ) -> Dict[str, Any]:
        mutation = DELETE_PROJECT_MUTATION if permanently else ARCHIVE_PROJECT_MUTATION
        variables = {"projectId": project_id}

        result = await self._call_linear_api(mutation, variables)

        if permanently:
            success = result.get("projectDelete", {}).get("success", False)
            action = "deleted"
        else:
            success = result.get("projectArchive", {}).get("success", False)
            action = "archived"

        if success:
            logger.info(f"Successfully {action} Linear project: {project_id}")
        else:
            logger.warning(f"Failed to {action} Linear project: {project_id}")

        return {"success": success}

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        variables = {"projectId": project_id}
        result = await self._call_linear_api(CHECK_PROJECT_EXISTS_QUERY, variables)

        project = result.get("project")

        return project

    async def check_project_exists(self, project_id: str) -> bool:
        try:
            project = await self.get_project(project_id)
            return project is not None
        except Exception as e:
            logger.error(f"Error checking project existence: {str(e)}")
            return False

    # ============ Project Milestone===========

    async def create_project_milestone(
        self, milestone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if "name" not in milestone_data:
            raise ValueError("Milestone name is required")

        if "projectId" not in milestone_data:
            raise ValueError("Project ID is required")

        variables = {"input": milestone_data}
        result = await self._call_linear_api(
            CREATE_PROJECT_MILESTONE_MUTATION, variables
        )

        milestone = result.get("projectMilestoneCreate", {}).get("projectMilestone", {})
        if not milestone:
            raise Exception("Failed to create project milestone in Linear")

        return milestone

    async def update_project_milestone(
        self, milestone_id: str, milestone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        cleaned_data = {}

        if milestone_data.get("name"):
            cleaned_data["name"] = str(milestone_data["name"])

        if milestone_data.get("description"):
            cleaned_data["description"] = str(milestone_data["description"])

        if milestone_data.get("targetDate"):
            cleaned_data["targetDate"] = milestone_data["targetDate"]

        if "sortOrder" in milestone_data:
            cleaned_data["sortOrder"] = float(milestone_data["sortOrder"])

        if not cleaned_data:
            logger.warning(f"No valid fields to update for milestone {milestone_id}")
            return {"id": milestone_id}

        variables = {"id": str(milestone_id), "input": cleaned_data}

        result = await self._call_linear_api(
            UPDATE_PROJECT_MILESTONE_MUTATION, variables
        )

        milestone = result.get("projectMilestoneUpdate", {}).get("projectMilestone", {})
        if not milestone:
            raise Exception(f"Failed to update milestone {milestone_id} in Linear")

        return milestone

    async def delete_project_milestone(self, milestone_id: str) -> Dict[str, Any]:
        variables = {"id": str(milestone_id)}

        result = await self._call_linear_api(
            DELETE_PROJECT_MILESTONE_MUTATION, variables
        )

        success = result.get("projectMilestoneDelete", {}).get("success", False)

        return {"success": success}

    async def get_project_milestone(
        self, milestone_id: str
    ) -> Optional[Dict[str, Any]]:
        variables = {"id": str(milestone_id)}
        result = await self._call_linear_api(GET_PROJECT_MILESTONE_QUERY, variables)
        milestone = result.get("projectMilestone")
        return milestone

    async def check_project_milestone_exists(self, milestone_id: str) -> bool:
        try:
            milestone = await self.get_project_milestone(milestone_id)
            return milestone is not None
        except Exception as e:
            logger.error(f"Error checking milestone existence: {str(e)}")
            return False

    async def list_project_milestones(self, project_id: str) -> list:
        variables = {"projectId": str(project_id)}
        result = await self._call_linear_api(LIST_PROJECT_MILESTONES_QUERY, variables)

        project = result.get("project", {})
        milestones = project.get("projectMilestones", {}).get("nodes", [])

        return milestones

    # ----------- Project Update Operations -----------
    async def create_project_update(
        self, project_id: str, body: str, health: str = "onTrack"
    ) -> Dict[str, Any]:
        valid_health = ["onTrack", "atRisk", "offTrack", "complete"]
        if health not in valid_health:
            health = "onTrack"

        update_data = {"projectId": str(project_id), "body": body, "health": health}

        variables = {"input": update_data}

        result = await self._call_linear_api(CREATE_PROJECT_UPDATE_MUTATION, variables)

        project_update = result.get("projectUpdateCreate", {}).get("projectUpdate", {})

        if not project_update:
            raise Exception(f"Failed to create project update for project {project_id}")

        return project_update

    async def get_project_update(self, update_id: str) -> Optional[Dict[str, Any]]:
        """Get project update by ID"""

        variables = {"id": str(update_id)}
        result = await self._call_linear_api(GET_PROJECT_UPDATE_QUERY, variables)

        return result.get("projectUpdate")

    async def list_project_updates(self, project_id: str) -> list:
        """List all project updates for a project"""

        variables = {"projectId": str(project_id)}
        result = await self._call_linear_api(LIST_PROJECT_UPDATES_QUERY, variables)

        project = result.get("project", {})
        updates = project.get("projectUpdates", {}).get("nodes", [])

        return updates

    async def get_or_create_discussion_update(self, project_id: str) -> Dict[str, Any]:
        try:
            # Check if "Discussion" update already exists
            updates = await self.list_project_updates(project_id)

            for update in updates:
                if update.get("body", "").startswith("[Discussion]"):
                    logger.info(f"Found existing discussion update: {update['id']}")
                    return update

            discussion_update = await self.create_project_update(
                project_id=project_id,
                body="[Discussion] Thảo luận về dự án",
                health="onTrack",
            )

            return discussion_update

        except Exception as e:
            logger.error(f"Failed to get/create discussion update: {str(e)}")
            raise


# Helper functions for mapping
def get_linear_status_id(status_name: str) -> Optional[str]:
    """Map internal status to Linear state ID"""
    status_map = {
        "DRAFT": "a291583a-c46a-4096-9df7-ad9046cd39fd",
        "ACTIVE": "a291583a-c46a-4096-9df7-ad9046cd39fd",
        "IN_PROGRESS": "022d6dca-d63c-4ee0-9768-40a3c2d99592",
        "PLANNED": "2d517b0e-9395-40ba-a1fa-e1986ee76c7c",
        "COMPLETED": "3f192138-2d5e-4cc1-97ee-08bd54df6130",
        "CANCELED": "c4d86fca-29ca-48b1-8a2c-168a7f954d23",
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
    label_map = {"ARCHITECTURE": "c78c123d-4c44-5d5e-6a62-78d1ef73c71d"}
    return label_map.get(category_name.upper())


def map_priority(priority_value: str) -> int:
    """Map priority string to Linear priority number (1-4)"""
    priority_map = {"URGENT": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4, "NO_PRIORITY": 0}
    return priority_map.get(priority_value.upper(), 3)
