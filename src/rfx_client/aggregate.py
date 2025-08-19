from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR, logger, timestamp
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from isodate import parse_duration
from .types import Priority, SyncStatus


class CPOPortalAggregate(Aggregate):
    """CPO Portal Aggregate Root - Handles all project, work package, ticket, workflow, tag, integration, and notification operations"""

    # =========== Estimator (Project Context) ============
    @action('estimator-created', resources='project')
    async def create_project_estimator(self, /, data):
        # create a new project with the data
        """Create a new estimator (project draft)"""
        profile_id = self.get_context().profile_id
        estimator = await self.statemgr.find_one('_project', where={
            "members.ov": [profile_id],
            "status": "DRAFT"
        })
        if estimator:
            raise ValueError("Estimator already exists")

        estimator = self.init_resource(
            "project",
            serialize_mapping(data),
            status="DRAFT",
            _id=UUID_GENR()
        )
        # we will check user permission to add project-member role correct (now we just default it client)
        project_member = self.init_resource(
            "project-member",
            {
                "member_id": self.context.profile_id,
                "role": "CLIENT",
                "project_id": estimator._id
            },
            _id=UUID_GENR(),
        )

        await self.statemgr.insert(estimator)
        await self.statemgr.insert(project_member)
        return estimator

    @action('promotion-applied', resources='project')
    async def apply_promotion(self, /, data):
        """Apply a promotion code to a project"""
        project = self.rootobj
        logger.info(f"Project: {project}")
        promotion = await self.statemgr.find_one('promotion', where=dict(
            code=data.promotion_code
        ))

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

    # =========== Project (Project Context) ============

    @action('project-created', resources='project')
    async def create_project(self, /, data=None):
        try:
            parsed_duration = parse_duration(data.duration)
            data = data.set(duration=parsed_duration)
        except Exception:
            raise ValueError(f"Invalid duration format: {data.duration}")

        project = self.rootobj
        if project.status == "ACTIVE":
            raise ValueError(f"Already is a project")

        await self.statemgr.update(project, **serialize_mapping(data), status="ACTIVE", target_date=data.start_date + data.duration)
        new_project = await self.statemgr.find_one('project', where=dict(
            _id=project._id
        ))
        return new_project

    @action('project-updated', resources='project')
    async def update_project(self, /, data):
        """Update a project"""
        project = self.rootobj
        await self.statemgr.update(project, **serialize_mapping(data))
        return project

    @action('project-deleted', resources='project')
    async def delete_project(self, /):
        """Delete a project"""
        project = self.rootobj
        project_work_packages = await self.statemgr.find_all('project-work-package', where=dict(
            project_id=project._id
        ))

        await self.statemgr.invalidate(project)
        for project_work_package in project_work_packages:
            await self.statemgr.invalidate_one('project-work-package', project_work_package._id)

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
            project_work_item_data['project_id'] = project._id

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
                deliverable_data['project_id'] = project._id

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
            project_wp_work_item_data['project_id'] = project._id

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

    # =========== Project BDM Contact (Project Context) ============
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

    # =========== Promotion (Promotion Context) ============

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

    @action('promotion-removed', resources='promotion')
    async def remove_promotion(self, /, data):
        """Remove a promotion code"""
        promotion = self.rootobj
        await self.statemgr.invalidate(promotion)
        return promotion

    # =========== Project Member (Project Context) ============

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
        return record

    @action('member-removed', resources='project')
    async def remove_project_member(self, /, member_id: str):
        """Remove project member"""
        project = self.rootobj
        project_member = await self.statemgr.find_one('project-member', where=dict(
            project_id=project._id,
            member_id=member_id
        ))

        if not project_member:
            raise ValueError("Project member not found")

        await self.statemgr.invalidate_one('project-member', project_member._id)

    # =========== Project Milestone (Project Context) ============

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

    # =========== Project Category (Project Context) ============
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

    @action('project-category-updated', resources='project')
    async def update_project_category(self, /, data):
        """Update project category"""
        category = await self.statemgr.find_one('ref--project-category', where=dict(
            _id=data.project_category_id
        ))

        if not category:
            raise ValueError("Category not found")

        update_data = serialize_mapping(data)
        update_data.pop('project_category_id', None)

        await self.statemgr.update(category, **update_data)
        return category

    @action('project-category-deleted', resources='project')
    async def delete_project_category(self, /, data):
        """Delete project category"""
        await self.statemgr.invalidate_one('ref--project-category', data.project_category_id)

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
        try:
            parsed_estimate = parse_duration(data.estimate)
            data = data.set(estimate=parsed_estimate)
        except Exception:
            raise ValueError(f"Invalid estimate format: {data.estimate}")

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

        if data.estimate:
            try:
                parsed_estimate = parse_duration(data.estimate)
                data = data.set(estimate=parsed_estimate)
            except Exception:
                raise ValueError(f"Invalid estimate format: {data.estimate}")

        await self.statemgr.update(work_item, **serialize_mapping(data))
        return work_item

    @action('work-item-invalidated', resources='work-item')
    async def invalidate_work_item(self, /, data):
        """Invalidate work item"""
        work_item = self.rootobj
        await self.statemgr.invalidate(work_item)
        return work_item

    # =========== Work Item Deliverable (Work Item Context) ============
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

    # =========== Work Item to Work Package (Work Package Context) ============
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

    @action('work-item-removed-from-work-package', resources='work-package')
    async def remove_work_item_from_work_package(self, /, work_item_id):
        """Remove work item from work package"""
        work_package = self.rootobj
        work_package_work_item = await self.statemgr.find_one('work-package-work-item', where=dict(
            work_package_id=work_package._id,
            work_item_id=work_item_id
        ))
        if not work_package_work_item:
            raise ValueError("Work item not found")

        await self.statemgr.invalidate_one('work-package-work-item', work_package_work_item._id)

    # =========== Work Item Type (Work Item Context) ============

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
        work_item_type = await self.statemgr.find_one('ref--work-item-type', where=dict(
            _id=data.work_item_type_id
        ))

        if not work_item_type:
            raise ValueError("Work item type not found")

        update_data = serialize_mapping(data)
        update_data.pop('work_item_type_id', None)

        await self.statemgr.update(work_item_type, **update_data)
        return work_item_type

    @action('work-item-type-invalidated', resources='work-item')
    async def invalidate_work_item_type(self, /, data):
        """Invalidate work item type"""
        work_item_type = await self.statemgr.find_one('ref--work-item-type', where=dict(
            _id=data.work_item_type_id
        ))

        if not work_item_type:
            raise ValueError("Work item type not found")

        await self.statemgr.invalidate_one('ref--work-item-type', work_item_type._id)
        return work_item_type

    # =========== Project Work Item (Project Context) ============

    @action('project-work-item-updated', resources='project')
    async def update_project_work_item(self, /, data):
        """Update project work item"""
        project_work_item = await self.statemgr.find_one('project-work-item', where=dict(
            _id=data.project_work_item_id,
            project_id=self.aggroot.identifier
        ))
        if not project_work_item:
            raise ValueError("Project work item not found")

        update_data = serialize_mapping(data)
        update_data.pop('project_work_item_id', None)

        await self.statemgr.update(project_work_item, **update_data)
        return project_work_item

    @action('project-work-item-invalidated', resources='project')
    async def invalidate_project_work_item(self, /, data):
        """Invalidate project work item"""
        project_work_item = await self.statemgr.find_one('project-work-item', where=dict(
            _id=data.project_work_item_id,
            project_id=self.aggroot.identifier
        ))
        if not project_work_item:
            raise ValueError("Project work item not found")

        await self.statemgr.invalidate_one('project-work-item', project_work_item._id)
        return project_work_item

# =========== Project Work Package (Project Context) ============

    @action('project-work-package-updated', resources='project')
    async def update_project_work_package(self, /, data):
        """Update project work package"""
        project_work_package = await self.statemgr.find_one('project-work-package', where=dict(
            _id=data.project_work_package_id,
            project_id=self.aggroot.identifier
        ))

        if not project_work_package:
            raise ValueError("Project work package not found")

        update_data = serialize_mapping(data)
        update_data.pop('project_work_package_id', None)

        await self.statemgr.update(project_work_package, **update_data)
        return project_work_package

# =========== Project Work Package Work Item (Project Context) ============

    @action("add-new-work-item-to-project-work-package", resources='project')
    # =========== Project Work Package Work Item (Project Context) ============
    @action("add-new-work-item-to-project-work-package", resources='project')
    async def add_new_work_item_to_project_work_package(self, /, data):
        """Add new work item to project work package and clone into project work item"""

        project_work_package = await self.statemgr.find_one(
            "project-work-package",
            where=dict(
                _id=data.project_work_package_id,
                project_id=self.aggroot.identifier
            )
        )
        if not project_work_package:
            raise ValueError("Project work package not found")

        work_item = await self.statemgr.find_one(
            "work-item",
            where=dict(_id=data.work_item_id)
        )
        if not work_item:
            raise ValueError("Work item not found")

        project_work_item_data = {
            "_id": UUID_GENR(),
            "project_id": self.aggroot.identifier,
            "name": work_item.name,
            "type": work_item.type,
            "description": work_item.description,
            "price_unit": work_item.price_unit,
            "credit_per_unit": work_item.credit_per_unit,
            "estimate": work_item.estimate,
        }
        project_work_item = self.init_resource(
            "project-work-item",
            serialize_mapping(project_work_item_data)
        )
        await self.statemgr.insert(project_work_item)

        link_data = {
            "project_work_package_id": project_work_package._id,
            "project_work_item_id": project_work_item._id,
            "project_id": self.aggroot.identifier
        }
        record = self.init_resource(
            "project-work-package-work-item",
            serialize_mapping(link_data)
        )
        await self.statemgr.insert(record)

    @action("remove-project-work-item-from-project-work-package", resources='project')
    async def remove_project_work_item_from_project_work_package(self, /, data):
        """Remove project work item from project work package"""
        project_work_item = await self.statemgr.find_one('project-work-item', where=dict(
            _id=data.project_work_item_id,
            project_id=self.aggroot.identifier
        ))
        if not project_work_item:
            raise ValueError("Project work item not found")

        project_work_package_work_item = await self.statemgr.find_one('project-work-package-work-item', where=dict(
            project_work_package_id=data.project_work_package_id,
            project_work_item_id=project_work_item._id,
            project_id=self.aggroot.identifier
        ))
        if not project_work_package_work_item:
            raise ValueError("Project work package work item not found")

        await self.statemgr.invalidate_one('project-work-package-work-item', project_work_package_work_item._id)
        await self.statemgr.invalidate_one('project-work-item', project_work_item._id)

# =========== Project Work Item Deliverable (Project Context) ============

    @action('project-work-item-deliverable-updated', resources='project')
    async def update_project_work_item_deliverable(self, /, data):
        """Update project work item deliverable"""
        project_work_item_deliverable = await self.statemgr.find_one('project-work-item-deliverable', where=dict(
            _id=data.project_work_item_deliverable_id,
            project_id=self.aggroot.identifier
        ))

        if not project_work_item_deliverable:
            raise ValueError("Project work item deliverable not found")

        update_data = serialize_mapping(data)
        update_data.pop('project_work_item_deliverable_id', None)

        await self.statemgr.update(project_work_item_deliverable, **update_data)
        return project_work_item_deliverable

    @action('project-work-item-deliverable-invalidated', resources='project')
    async def invalidate_project_work_item_deliverable(self, /, data):
        """Invalidate project work item deliverable"""
        project_work_item_deliverable = await self.statemgr.find_one('project-work-item-deliverable', where=dict(
            _id=data.project_work_item_deliverable_id,
            project_id=self.aggroot.identifier
        ))
        if not project_work_item_deliverable:
            raise ValueError("Project work item deliverable not found")

        await self.statemgr.invalidate_one(
            'project-work-item-deliverable', project_work_item_deliverable._id)
        return project_work_item_deliverable
