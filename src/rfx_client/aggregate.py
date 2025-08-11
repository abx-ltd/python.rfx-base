from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR, logger, timestamp
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from isodate import parse_duration
from .types import Priority, SyncStatus


class CPOPortalAggregate(Aggregate):
    """CPO Portal Aggregate Root - Handles all project, work package, ticket, workflow, tag, integration, and notification operations"""

    # =========== Project Context ============
    @action('estimator-created', resources='project')
    async def create_project_estimator(self, /, data):

        # create a new project with the data
        """Create a new estimator (project draft)"""
        record = self.init_resource(
            "project",
            serialize_mapping(data),
            status="DRAFT",
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action('project-created', resources='project')
    async def create_project(self, /, data=None):
        try:
            parsed_duration = parse_duration(data.duration)
            data = data.set(duration=parsed_duration)
        except Exception:
            raise ValueError(f"Invalid duration format: {data.duration}")

        project = self.rootobj
        result = await self.statemgr.update(project, **serialize_mapping(data), status="ACTIVE", target_date=data.start_date + parsed_duration)
        return result

    @action('project-bdm-contact-created', resources='project')
    async def create_project_bdm_contact(self, /, data):
        project = self.rootobj
        """Create a new BDM contact for a project"""
        record = self.init_resource(
            "project-bdm-contact",
            serialize_mapping(data),
            project_id=project._id,
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action('project-bdm-contact-updated', resources='project')
    async def update_project_bdm_contact(self, /, data):
        project = self.rootobj
        """Update a project BDM contact"""
        record = await self.statemgr.find_one('project-bdm-contact', where=dict(
            project_id=project._id,
            _id=data.bdm_contact_id
        ))

        if not record:
            raise ValueError("BDM contact not found")

        update_data = serialize_mapping(data)
        update_data.pop('bdm_contact_id', None)

        await self.statemgr.update(record, **update_data)
        return record

    @action('project-bdm-contact-deleted', resources='project')
    async def delete_project_bdm_contact(self, /, data):
        project = self.rootobj
        """Delete a project BDM contact"""
        record = await self.statemgr.find_one('project-bdm-contact', where=dict(
            _id=data.bdm_contact_id,
            project_id=project._id
        ))

        if not record:
            raise ValueError(
                "BDM contact not found or does not belong to this project")

        await self.statemgr.invalidate(record)

    @action('promotion-applied', resources='project')
    async def apply_promotion(self, /, data):
        """Apply a promotion code to a project"""
        project = self.rootobj
        logger.info(f"Project: {project}")
        promotion = await self.statemgr.find_one('promotion', where=dict(
            code=data.promotion_code
        ))

        logger.info(f"Promotion: {promotion}")

        if not promotion:
            raise ValueError("Promotion code not found")

        if promotion.max_uses <= promotion.current_uses:
            raise ValueError(
                "Promotion code has reached the maximum number of uses")

        now = datetime.now(timezone.utc)
        if promotion.valid_from > now or promotion.valid_until < now:
            raise ValueError("Promotion code is not valid")

        await self.statemgr.update(promotion, current_uses=promotion.current_uses + 1)
        await self.statemgr.update(project, referral_code_used=promotion.code)

    @action('promotion-created', resources='promotion')
    async def create_promotion(self, /, data):
        record = self.init_resource(
            "promotion",
            serialize_mapping(data),
            _id=UUID_GENR()
        )
        """Create a new promotion code"""
        await self.statemgr.insert(record)
        return record

    @action('promotion-updated', resources='promotion')
    async def update_promotion(self, /, data):
        promotion = self.rootobj
        await self.statemgr.update(promotion, **serialize_mapping(data))
        return promotion

    @action('ticket-added-to-project', resources='project')
    async def add_ticket_to_project(self, /, data):
        project_id = self.aggroot.identifier
        """Add ticket to project"""
        record = self.init_resource(
            "project-ticket",
            {
                "project_id": project_id,
                "ticket_id": data.ticket_id
            }
        )
        await self.statemgr.insert(record)
        return record

    @action('work-package-added', resources='project')
    async def add_work_package_to_estimator(self, /, data):
        """Add work package to estimator and clone all related work items"""
        project = self.rootobj

        work_package = await self.statemgr.find_one('work-package', where=dict(
            _id=data.work_package_id
        ))
        if not work_package:
            raise ValueError("Work package not found")

        project_work_package = self.init_resource(
            "project-work-package",
            {
                "work_package_id": data.work_package_id,
                "project_id": project._id,
                "work_package_name": work_package.work_package_name,
                "work_package_description": work_package.description,
                "work_package_example_description": work_package.example_description,
                "work_package_is_custom": work_package.is_custom,
                "work_package_complexity_level": work_package.complexity_level,
                "work_package_estimate": work_package.estimate
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(project_work_package)

        work_package_work_items = await self.statemgr.find_all('work-package-work-item', where=dict(
            work_package_id=data.work_package_id
        ))

        if not work_package_work_items:
            return project_work_package

        work_item_ids = [
            wp_work_item.work_item_id for wp_work_item in work_package_work_items]

        original_work_items = await self.statemgr.find_all('work-item', where={
            '_id.in': work_item_ids
        })

        work_item_lookup = {item._id: item for item in original_work_items}

        all_deliverables = await self.statemgr.find_all('work-item-deliverable', where={
            'work_item_id.in': work_item_ids
        })
        deliverables_by_work_item = {}
        for deliverable in all_deliverables:
            work_item_id = deliverable.work_item_id
            if work_item_id not in deliverables_by_work_item:
                deliverables_by_work_item[work_item_id] = []
            deliverables_by_work_item[work_item_id].append(deliverable)

        project_work_items_batch = []
        project_deliverables_batch = []
        project_wp_work_items_batch = []

        project_work_item_mapping = {}

        for wp_work_item in work_package_work_items:
            logger.info(
                f"Processing wp_work_item with work_item_id: {wp_work_item.work_item_id}")
            original_work_item = work_item_lookup.get(
                wp_work_item.work_item_id)

            if not original_work_item:
                logger.warning(
                    f"Original work item not found for ID: {wp_work_item.work_item_id}")
                continue

            project_work_item_data = serialize_mapping(original_work_item)
            project_work_item_data.pop('_created', None)
            project_work_item_data.pop('_updated', None)
            project_work_item_data.pop('_etag', None)

            project_work_item_id = UUID_GENR()
            project_work_item_data['_id'] = project_work_item_id

            project_work_items_batch.append(project_work_item_data)

            project_work_item_mapping[original_work_item._id] = project_work_item_id

            work_item_deliverables = deliverables_by_work_item.get(
                wp_work_item.work_item_id, [])

            for deliverable in work_item_deliverables:
                deliverable_data = serialize_mapping(deliverable)
                deliverable_data.pop('_id', None)
                deliverable_data.pop('_created', None)
                deliverable_data.pop('_updated', None)
                deliverable_data.pop('_etag', None)
                deliverable_data.pop('work_item_id', None)
                deliverable_data['project_work_item_id'] = project_work_item_id
                deliverable_data['_id'] = UUID_GENR()

                project_deliverables_batch.append(deliverable_data)

            project_wp_work_item_data = serialize_mapping(wp_work_item)
            project_wp_work_item_data.pop('_id', None)
            project_wp_work_item_data.pop('_created', None)
            project_wp_work_item_data.pop('_updated', None)
            project_wp_work_item_data.pop('_etag', None)
            project_wp_work_item_data.pop(
                'work_package_id', None)
            project_wp_work_item_data.pop(
                'work_item_id', None)
            project_wp_work_item_data['project_work_package_id'] = project_work_package._id
            project_wp_work_item_data['project_work_item_id'] = project_work_item_id
            project_wp_work_item_data['_id'] = UUID_GENR()

            project_wp_work_items_batch.append(project_wp_work_item_data)

        if project_work_items_batch:
            await self.statemgr.insert_many("project-work-item", *project_work_items_batch)

        if project_deliverables_batch:
            await self.statemgr.insert_many("project-work-item-deliverable", *project_deliverables_batch)

        if project_wp_work_items_batch:
            await self.statemgr.insert_many("project-work-package-work-item", *project_wp_work_items_batch)

        return project_work_package

    @action('work-package-removed', resources='project')
    async def remove_work_package_from_estimator(self, /, data):
        """Remove a work package and all related items from the project estimator"""
        project = self.rootobj

        # 1. Find project-work-package
        project_work_package = await self.statemgr.find_one('project-work-package', where=dict(
            work_package_id=data.work_package_id,
            project_id=project._id
        ))

        if not project_work_package:
            raise ValueError("Work package not found")

        wp_work_items_to_remove = await self.statemgr.find_all(
            'project-work-package-work-item',
            where=dict(project_work_package_id=project_work_package._id)
        )

        if not wp_work_items_to_remove:
            # if no work item, just delete work package and return
            await self.statemgr.invalidate_one('project-work-package', project_work_package._id)
            return None

        # 2. get project_work_item_id from all records
        project_work_item_ids = [
            item.project_work_item_id for item in wp_work_items_to_remove
        ]

        # 3. delete all project-work-item-deliverable related to project_work_item
        project_deliverables = await self.statemgr.find_all(
            'project-work-item-deliverable',
            where={'project_work_item_id.in': project_work_item_ids}
        )
        for deliverable in project_deliverables:
            await self.statemgr.invalidate_one('project-work-item-deliverable', deliverable._id)

        # 4. delete all project-work-item
        project_work_items = await self.statemgr.find_all(
            'project-work-item',
            where={'_id.in': project_work_item_ids}
        )
        for work_item in project_work_items:
            await self.statemgr.invalidate_one('project-work-item', work_item._id)

        # 5. delete all project-work-package-work-item
        for wp_work_item in wp_work_items_to_remove:
            await self.statemgr.invalidate_one('project-work-package-work-item', wp_work_item._id)

        # 6. delete project-work-package
        await self.statemgr.invalidate_one('project-work-package', project_work_package._id)

        return None

    @action('member-added', resources='project')
    async def add_project_member(self, /, member_id: str, role: str):
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
        await self.statemgr.insert(record)

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
    async def create_project_milestone(self, /, data):
        project = self.rootobj
        record = self.init_resource(
            "project-milestone",
            serialize_mapping(data),
            _id=UUID_GENR(),
            project_id=project._id
        )
        await self.statemgr.insert(record)
        return record

    @action('milestone-updated', resources='project')
    async def update_project_milestone(self, /, data):
        """Update project milestone"""
        milestone = await self.statemgr.find_one('project-milestone', where=dict(
            _id=data.milestone_id,
            project_id=self.aggroot.identifier
        ))

        if not milestone:
            raise ValueError(
                "Milestone not found or does not belong to this project")

        update_data = serialize_mapping(data)
        update_data.pop('milestone_id', None)

        await self.statemgr.update(milestone, **update_data)

    @action('milestone-deleted', resources='project')
    async def delete_project_milestone(self, /, data):
        """Delete project milestone"""
        await self.statemgr.invalidate_one('project-milestone', data.milestone_id)

    @action('resource-uploaded', resources='project')
    async def upload_project_resource(self, /, file: bytes, type: Optional[str] = None, description: Optional[str] = None) -> str:
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
        await self.statemgr.insert(record)
        return str(resource_id)

    @action('resource-deleted', resources='project')
    async def delete_project_resource(self, /, resource_id: str):
        """Delete project resource"""
        await self.statemgr.invalidate_one("project-resource", resource_id)

    @action('project-category-created', resources='project')
    async def create_project_category(self, /, data):
        """Create project category"""
        record = self.init_resource(
            "ref--project-category",
            serialize_mapping(data),
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    # =========== Work Package Context ============

    @action('work-package-created', resources='work-package')
    async def create_work_package(self, /, data):
        """Create new work package"""
        record = self.init_resource(
            "work-package",
            serialize_mapping(data),
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action('work-package-updated', resources='work-package')
    async def update_work_package(self, /, data):
        """Update work package details"""
        work_package = self.rootobj
        await self.statemgr.update(work_package, **serialize_mapping(data))
        return work_package

    @action('work-package-invalidated', resources='work-package')
    async def invalidate_work_package(self, /):
        """Invalidate work package"""
        work_package = self.rootobj
        await self.statemgr.invalidate(work_package)
        return work_package

    # =========== Work Item Context ============

    @action('work-item-created', resources='work-item')
    async def create_work_item(self, /, data):
        """Create new work item"""
        record = self.init_resource(
            "work-item",
            serialize_mapping(data),
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action('work-item-updated', resources='work-item')
    async def update_work_item(self, /, data):
        """Update work item"""
        work_item = self.rootobj
        await self.statemgr.update(work_item, **serialize_mapping(data))
        return work_item

    @action('work-item-invalidated', resources='work-item')
    async def invalidate_work_item(self, /, data):
        """Invalidate work item"""
        work_item = self.rootobj
        await self.statemgr.invalidate(work_item)
        return work_item

    @action('work-item-deliverable-created', resources='work-item')
    async def create_work_item_deliverable(self, /, data):
        """Create new work item deliverable"""
        record = self.init_resource(
            "work-item-deliverable",
            serialize_mapping(data),
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action('work-item-deliverable-updated', resources='work-item')
    async def update_work_item_deliverable(self, /, data):
        """Update work item deliverable"""
        work_item_deliverable = await self.statemgr.find_one('work-item-deliverable', where=dict(
            _id=data.work_item_deliverable_id,
            work_item_id=self.rootobj._id
        ))
        if not work_item_deliverable:
            raise ValueError("Work item deliverable not found")

        update_data = serialize_mapping(data)
        update_data.pop('work_item_deliverable_id', None)

        result = await self.statemgr.update(work_item_deliverable, **update_data)
        return result

    @action('work-item-deliverable-invalidated', resources='work-item')
    async def invalidate_work_item_deliverable(self, /, data):
        """Invalidate work item deliverable"""
        deliverable = await self.statemgr.find_one('work-item-deliverable', where=dict(
            work_item_id=self.rootobj._id,
            _id=data.work_item_deliverable_id
        ))
        if deliverable:
            await self.statemgr.invalidate_one('work-item-deliverable', deliverable._id)
        else:
            raise ValueError("Work item deliverable not found")

    @action('work-item-added-to-work-package', resources='work-package')
    async def add_work_item_to_work_package(self, /, work_item_id):
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
        await self.statemgr.insert(record)
        return record

    @action('work-item-type-created', resources='work-item')
    async def create_work_item_type(self, /, data):
        """Create new work item type"""
        record = self.init_resource(
            "ref--work-item-type",
            serialize_mapping(data),
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action('work-item-type-updated', resources='work-item')
    async def update_work_item_type(self, /, data):
        """Update work item type"""
        work_item_type = self.rootobj
        await self.statemgr.update(work_item_type, **serialize_mapping(data))
        return work_item_type

    @action('work-item-type-invalidated', resources='work-item')
    async def invalidate_work_item_type(self, /, data):
        """Invalidate work item type"""
        work_item_type = self.rootobj
        await self.statemgr.invalidate(work_item_type)
        return work_item_type

    @action('work-item-type-deleted', resources='work-item')
    # =========== Integration Context ============
    @action('integration-sync', resources='integration')
    async def unified_sync(self, /, data):
        """Unified sync method for integrations"""

    # =========== Notification Context ============
    @action('notification-marked-read', resources='notification')
    async def mark_notification_as_read(self, /, notification_id: str):
        """Mark notification as read"""

    @action('all-notifications-marked-read', resources='notification')
    async def mark_all_notifications_as_read(self, /):
        """Mark all notifications as read"""
