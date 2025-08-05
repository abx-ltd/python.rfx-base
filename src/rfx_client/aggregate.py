from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from typing import Optional, Dict, Any
from datetime import datetime
from isodate import parse_duration
from .types import Priority, SyncStatus


class CPOPortalAggregate(Aggregate):
    """CPO Portal Aggregate Root - Handles all project, work package, ticket, workflow, tag, integration, and notification operations"""

    # =========== Project Context ============
    @action('estimator-created', resources='project')
    async def create_project_estimator(self, stm, /, data):

        # create a new project with the data
        """Create a new estimator (project draft)"""
        record = self.init_resource(
            "project",
            serialize_mapping(data),
            status="DRAFT",
            _id=UUID_GENR()
        )
        await stm.insert(record)
        return record

    @action('project-created', resources='project')
    async def create_project(self, stm, /, data=None):
        try:
            parsed_duration = parse_duration(data.duration)
            data = data.set(duration=parsed_duration)
        except Exception:
            raise ValueError(f"Invalid duration format: {data.duration}")

        project = self.rootobj
        result = await stm.update(project, **serialize_mapping(data), status="ACTIVE", target_date=data.start_date + parsed_duration)
        return result

    @action('project-bdm-contact-created', resources='project')
    async def create_project_bdm_contact(self, stm, /, data):
        project = self.rootobj
        """Create a new BDM contact for a project"""
        record = self.init_resource(
            "project-bdm-contact",
            serialize_mapping(data),
            project_id=project._id
        )
        await stm.insert(record)
        return record

    @action('project-bdm-contact-updated', resources='project')
    async def update_project_bdm_contact(self, stm, /, data):
        project = self.rootobj
        """Update a project BDM contact"""
        record = await stm.find_one('project-bdm-contact', where=dict(
            project_id=project._id,
            _id=data.bdm_contact_id
        ))

        if not record:
            raise ValueError("BDM contact not found")

        update_data = serialize_mapping(data)
        update_data.pop('bdm_contact_id', None)

        await stm.update(record, **update_data)
        return record

    @action('project-bdm-contact-deleted', resources='project')
    async def delete_project_bdm_contact(self, stm, /, data):
        project = self.rootobj
        """Delete a project BDM contact"""
        record = await stm.find_one('project-bdm-contact', where=dict(
            _id=data.bdm_contact_id,
            project_id=project._id
        ))

        if not record:
            raise ValueError(
                "BDM contact not found or does not belong to this project")

        await stm.invalidate(record)

    @action('promotion-created', resources='promotion')
    async def create_promotion(self, stm, /, data):
        record = self.init_resource(
            "promotion",
            serialize_mapping(data)
        )
        """Create a new promotion code"""
        await stm.insert(record)
        return record

    @action('promotion-updated', resources='promotion')
    async def update_promotion(self, stm, /, data):
        promotion = self.rootobj
        await stm.update(promotion, **serialize_mapping(data))
        return promotion

    @action('ticket-added-to-project', resources='project')
    async def add_ticket_to_project(self, stm, /, data):
        project_id = self.aggroot.identifier
        """Add ticket to project"""
        record = self.init_resource(
            "project-ticket",
            {
                "project_id": project_id,
                "ticket_id": data.ticket_id
            }
        )
        await stm.insert(record)
        return record

    @action('work-package-added', resources='project')
    async def add_work_package_to_estimator(self, stm, /, data):
        """Add work package to estimator"""
        project = self.rootobj

        record = self.init_resource(
            "project-work-package",
            {
                "work_package_id": data.work_package_id,
                # "quantity": data.quantity,
                "project_id": project._id
            },
            _id=UUID_GENR(),
        )
        await stm.insert(record)
        return record

    @action('member-added', resources='project')
    async def add_project_member(self, stm, /, member_id: str, role: str):
        project = self.rootobj

        """Add member to project"""
        record = self.init_resource(
            "project-member",
            {
                "member_id": member_id,
                "role": role,
                "project_id": project._id
            },
            _id=UUID_GENR(),
        )
        await stm.insert(record)

    # @action('team-assigned', resources='project')
    # async def assign_team_to_project(self, stm, /, team_id: str, role: str):
    #     """Assign team to project"""
    #     record = self.init_resource(
    #         "project-member",
    #         {
    #             "team_id": team_id,
    #             "role": role,
    #             "project_id": self.aggroot.identifier
    #         },
    #         _id=UUID_GENR(),
    #     )
    #     await stm.insert(record)

    # @action('member-removed', resources='project')
    # async def remove_project_member(self, stm, /, member_id: str):
    #     """Remove project member"""
    #     members = await stm.find_all('project-member',
    #                                  where=dict(
    #                                      project_id=self.aggroot.identifier,
    #                                      team_id=member_id
    #                                  ))
    #     for member in members:
    #         await stm.invalidate_one('project-member', member._id)

    @action('milestone-created', resources='project')
    async def create_project_milestone(self, stm, /, data):
        project = self.rootobj
        record = self.init_resource(
            "project-milestone",
            serialize_mapping(data),
            _id=UUID_GENR(),
            project_id=project._id
        )
        await stm.insert(record)
        return record

    @action('milestone-updated', resources='project')
    async def update_project_milestone(self, stm, /, data):
        """Update project milestone"""
        milestone = await stm.find_one('project-milestone', where=dict(
            _id=data.milestone_id,
            project_id=self.aggroot.identifier
        ))

        if not milestone:
            raise ValueError(
                "Milestone not found or does not belong to this project")

        update_data = serialize_mapping(data)
        update_data.pop('milestone_id', None)

        await stm.update(milestone, **update_data)

    @action('milestone-deleted', resources='project')
    async def delete_project_milestone(self, stm, /, data):
        """Delete project milestone"""
        await stm.invalidate_one('project-milestone', data.milestone_id)

    @action('resource-uploaded', resources='project')
    async def upload_project_resource(self, stm, /, file: bytes, type: Optional[str] = None, description: Optional[str] = None) -> str:
        """Upload project resource"""
        resource_id = UUID_GENR()
        record = self.init_resource(
            "project-resource",
            {
                "type": type,
                "description": description,
                "size": len(file),
                "project_id": self.aggroot.identifier
            },
            _id=resource_id,
            uploaded_at=datetime.utcnow()
        )
        await stm.insert(record)
        return str(resource_id)

    @action('resource-deleted', resources='project')
    async def delete_project_resource(self, stm, /, resource_id: str):
        """Delete project resource"""
        await stm.invalidate_one("project-resource", resource_id)

    @action('project-category-created', resources='project')
    async def create_project_category(self, stm, /, data):
        """Create project category"""
        record = self.init_resource(
            "ref--project-category",
            serialize_mapping(data),
        )
        await stm.insert(record)
        return record

    # =========== Work Package Context ============

    @action('work-package-created', resources='work-package')
    async def create_work_package(self, stm, /, data):
        """Create new work package"""
        record = self.init_resource(
            "work-package",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

    @action('work-package-updated', resources='work-package')
    async def update_work_package(self, stm, /, data):
        """Update work package details"""
        work_package = self.rootobj
        await stm.update(work_package, **serialize_mapping(data))
        return work_package

    @action('work-package-invalidated', resources='work-package')
    async def invalidate_work_package(self, stm, /):
        """Invalidate work package"""
        work_package = self.rootobj
        await stm.invalidate(work_package)
        return work_package

    @action('work-item-deliverable-created', resources='work-item')
    async def create_work_item_deliverable(self, stm, /, data):
        """Create new work item deliverable"""
        record = self.init_resource(
            "work-item-deliverable",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

    @action('work-item-deliverable-invalidated', resources='work-item')
    async def invalidate_work_item_deliverable(self, stm, /, data):
        """Invalidate work item deliverable"""
        deliverable = await stm.find_one('work-item-deliverable', where=dict(
            work_item_id=self.rootobj._id,
            _id=data.deliverable_id
        ))
        if deliverable:
            await stm.invalidate_one('work-item-deliverable', deliverable._id)

    # =========== Work Item Context ============
    @action('work-item-created', resources='work-item')
    async def create_work_item(self, stm, /, data):
        """Create new work item"""
        record = self.init_resource(
            "work-item",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

    @action('work-item-added-to-work-package', resources='work-package')
    async def add_work_item_to_work_package(self, stm, /, work_item_id):
        """Add work item to work package"""
        work_package = self.rootobj
        data = {
            "work_package_id": work_package._id,
            "work_item_id": work_item_id
        }
        record = self.init_resource(
            "work-package-work-item",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

    @action('work-item-type-created', resources='work-item')
    async def create_work_item_type(self, stm, /, data):
        """Create new work item type"""
        record = self.init_resource(
            "ref--work-item-type",
            serialize_mapping(data)
        )
        await stm.insert(record)
        return record

    # =========== Integration Context ============
    @action('integration-sync', resources='integration')
    async def unified_sync(self, stm, /, data):
        """Unified sync method for integrations"""

    # =========== Notification Context ============
    @action('notification-marked-read', resources='notification')
    async def mark_notification_as_read(self, stm, /, notification_id: str):
        """Mark notification as read"""

    @action('all-notifications-marked-read', resources='notification')
    async def mark_all_notifications_as_read(self, stm, /):
        """Mark all notifications as read"""
