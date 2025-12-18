from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR, logger
from datetime import datetime, timezone
from .helper import parse_duration_for_db
from rfx_schema.rfx_client.types import SyncStatusEnum, InquiryStatusEnum
from . import config


class RFXClientAggregate(Aggregate):
    """CPO Portal Aggregate Root - Handles all project, work package, ticket, workflow, tag, integration, and notification operations"""

    # =========== Estimator (Project Context) ============
    @action("estimator-created", resources="project")
    async def create_project_estimator(self, /, data):
        # create a new project with the data
        """Create a new estimator (project draft)"""
        profile_id = self.get_context().profile_id
        estimator = await self.statemgr.exist(
            "_project", where={"members.ov": [profile_id], "status": "DRAFT"}
        )
        if estimator:
            raise ValueError("Estimator already exists")

        estimator = self.init_resource(
            "project",
            serialize_mapping(data),
            status="DRAFT",
            organization_id=self.context.organization_id,
            _id=self.aggroot.identifier,
        )
        # we will check user permission to add project-member role correct (now we just default it client)
        project_member = self.init_resource(
            "project_member",
            {
                "member_id": self.context.profile_id,
                "role": "CLIENT",
                "project_id": self.aggroot.identifier,
            },
            _id=UUID_GENR(),
        )

        await self.statemgr.insert(estimator)
        await self.statemgr.insert(project_member)
        return estimator

    @action("promotion-applied", resources="project")
    async def apply_promotion(self, /, data):
        """Apply a promotion code to a project"""
        project = self.rootobj
        promotion = await self.statemgr.find_one(
            "promotion", where=dict(code=data.promotion_code)
        )

        if not promotion:
            raise ValueError("Promotion code not found")

        if promotion.max_uses <= promotion.current_uses:
            raise ValueError("Promotion code has reached the maximum number of uses")

        now = datetime.now(timezone.utc)
        if promotion.valid_from > now or promotion.valid_until < now:
            raise ValueError("Promotion code is not valid")

        await self.statemgr.update(promotion, current_uses=promotion.current_uses + 1)
        await self.statemgr.update(project, referral_code_used=promotion.code)

    # =========== Project (Project Context) ============
    @action("project-created", resources="project")
    async def create_project(self, /, data=None):
        try:
            parsed_delta, duration_text, duration_interval = parse_duration_for_db(
                data.duration
            )
        except Exception:
            raise ValueError(f"Invalid duration format: {data.duration}")

        project = self.rootobj
        # if project.status == "ACTIVE":
        #     raise ValueError("Already is a project")

        target_date = data.start_date + parsed_delta

        data = data.set(duration=duration_interval)

        project_data = serialize_mapping(data)

        sync_status = SyncStatusEnum.PENDING
        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            sync_status = SyncStatusEnum.SYNCED

        await self.statemgr.update(
            project,
            **project_data,
            status="ACTIVE",
            target_date=target_date,
            duration_text=duration_text,
            sync_status=sync_status,
        )

        new_project = await self.statemgr.find_one(
            "project", where=dict(_id=project._id)
        )

        return new_project

    @action("project-updated", resources="project")
    async def update_project(self, /, data):
        """Update a project"""
        try:
            parsed_delta, duration_text, duration_interval = parse_duration_for_db(
                data.duration
            )
        except Exception:
            raise ValueError(f"Invalid duration format: {data.duration}")

        project = self.rootobj

        if data.status:
            status_id = await self.statemgr.get_status_id("project")

            to_status_key = await self.statemgr.has_status_key(status_id, data.status)

            if not to_status_key:
                raise ValueError("Invalid status")

            transition = await self.statemgr.has_status_transition(
                status_id, project.status, data.status
            )
            if not transition:
                raise ValueError("Invalid status, Can not transition to this status")

        project_data = serialize_mapping(data)
        project_data.pop("target_date", None)
        project_data.pop("duration", None)

        sync_status = SyncStatusEnum.PENDING
        if config.PROJECT_MANAGEMENT_INTEGRATION_ENABLED:
            sync_status = SyncStatusEnum.SYNCED

        await self.statemgr.update(
            project,
            **project_data,
            target_date=data.target_date,
            duration_text=duration_text,
            sync_status=sync_status,
        )
        return project

    @action("project-deleted", resources="project")
    async def delete_project(self, /):
        """Delete a project"""
        project = self.rootobj
        await self.statemgr.invalidate(project)

    @action("ticket-added-to-project", resources="ticket")
    async def add_ticket_to_project(self, /, data):
        ticket_id = self.aggroot.identifier
        """Add ticket to project"""
        record = self.init_resource(
            "project_ticket", {"project_id": data.project_id, "ticket_id": ticket_id}
        )
        await self.statemgr.insert(record)
        return record

    @action("work-package-added", resources="project")
    async def add_work_package_to_estimator(self, /, data):
        """Add work package to estimator and clone all related work items"""
        project = self.rootobj

        work_package = await self.statemgr.find_one(
            "work_package", where=dict(_id=data.work_package_id)
        )
        if not work_package:
            raise ValueError("Work package not found")

        project_work_package = self.init_resource(
            "project_work_package",
            {
                "work_package_id": data.work_package_id,
                "project_id": project._id,
                "work_package_name": work_package.work_package_name,
                "work_package_description": work_package.description,
                "work_package_example_description": work_package.example_description,
                "work_package_is_custom": False,
                "work_package_complexity_level": work_package.complexity_level,
                "work_package_estimate": work_package.estimate,
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(project_work_package)

        work_package_work_items = await self.statemgr.find_all(
            "work_package_work_item", where=dict(work_package_id=data.work_package_id)
        )

        if not work_package_work_items:
            return project_work_package

        work_item_ids = [
            wp_work_item.work_item_id for wp_work_item in work_package_work_items
        ]

        original_work_items = await self.statemgr.find_all(
            "work_item", where={"_id.in": work_item_ids}
        )

        work_item_lookup = {item._id: item for item in original_work_items}

        all_deliverables = await self.statemgr.find_all(
            "work_item_deliverable", where={"work_item_id.in": work_item_ids}
        )
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
            original_work_item = work_item_lookup.get(wp_work_item.work_item_id)

            if not original_work_item:
                continue

            project_work_item_data = serialize_mapping(original_work_item)
            project_work_item_data.pop("_created", None)
            project_work_item_data.pop("_updated", None)
            project_work_item_data.pop("_etag", None)
            project_work_item_data.pop("organization_id", None)

            project_work_item_id = UUID_GENR()
            project_work_item_data["_id"] = project_work_item_id
            project_work_item_data["project_id"] = project._id

            project_work_items_batch.append(project_work_item_data)

            project_work_item_mapping[original_work_item._id] = project_work_item_id

            work_item_deliverables = deliverables_by_work_item.get(
                wp_work_item.work_item_id, []
            )

            for deliverable in work_item_deliverables:
                deliverable_data = serialize_mapping(deliverable)
                deliverable_data.pop("_id", None)
                deliverable_data.pop("_created", None)
                deliverable_data.pop("_updated", None)
                deliverable_data.pop("_etag", None)
                deliverable_data.pop("work_item_id", None)
                deliverable_data["project_work_item_id"] = project_work_item_id
                deliverable_data["_id"] = UUID_GENR()
                deliverable_data["project_id"] = project._id

                project_deliverables_batch.append(deliverable_data)

            project_wp_work_item_data = serialize_mapping(wp_work_item)
            project_wp_work_item_data.pop("_id", None)
            project_wp_work_item_data.pop("_created", None)
            project_wp_work_item_data.pop("_updated", None)
            project_wp_work_item_data.pop("_etag", None)
            project_wp_work_item_data.pop("work_package_id", None)
            project_wp_work_item_data.pop("work_item_id", None)
            project_wp_work_item_data["project_work_package_id"] = (
                project_work_package._id
            )
            project_wp_work_item_data["project_work_item_id"] = project_work_item_id
            project_wp_work_item_data["_id"] = UUID_GENR()
            project_wp_work_item_data["project_id"] = project._id

            project_wp_work_items_batch.append(project_wp_work_item_data)

        if project_work_items_batch:
            await self.statemgr.insert_many(
                "project_work_item", *project_work_items_batch
            )
        if project_deliverables_batch:
            await self.statemgr.insert_many(
                "project_work_item_deliverable", *project_deliverables_batch
            )
        if project_wp_work_items_batch:
            await self.statemgr.insert_many(
                "project_work_package_work_item", *project_wp_work_items_batch
            )

        return project_work_package

    @action("custom-work-package-added", resources="project")
    async def add_custom_work_package(self, /, data):
        """Clone a project-work-package template (project_id NULL) into this project with all related records"""
        project = self.rootobj

        # --- STEP 1: Lấy project-work-package template ---
        template_pwp = await self.statemgr.find_one(
            "project_work_package",
            where=dict(_id=data.project_work_package_id, project_id=None),
        )
        if not template_pwp:
            raise ValueError(
                "Template project-work-package not found or not a template (project_id must be NULL)"
            )

        # --- STEP 2: Clone project-work-package ---
        new_pwp_id = UUID_GENR()
        pwp_data = serialize_mapping(template_pwp)
        pwp_data["_id"] = new_pwp_id
        pwp_data["project_id"] = project._id
        pwp_data.pop("_created", None)
        pwp_data.pop("_updated", None)
        pwp_data.pop("_etag", None)
        await self.statemgr.insert(self.init_resource("project_work_package", pwp_data))

        # --- STEP 3: Lấy các liên kết project-work-package-work-item ---
        template_links = await self.statemgr.find_all(
            "project_work_package_work_item",
            where=dict(project_work_package_id=data.project_work_package_id),
        )
        template_pwi_ids = [link.project_work_item_id for link in template_links]

        # --- STEP 4: Lấy các project-work-item ---
        template_pwis = []
        if template_pwi_ids:
            template_pwis = await self.statemgr.find_all(
                "project_work_item", where={"_id.in": template_pwi_ids}
            )

        # --- STEP 5: Lấy các deliverable ---
        template_deliverables = []
        if template_pwi_ids:
            template_deliverables = await self.statemgr.find_all(
                "project_work_item_deliverable",
                where={"project_work_item_id.in": template_pwi_ids},
            )

        # --- STEP 6: Chuẩn bị mapping id cũ → id mới ---
        pwi_id_map = {pwi._id: UUID_GENR() for pwi in template_pwis}
        deliverable_id_map = {d._id: UUID_GENR() for d in template_deliverables}
        link_id_map = {link._id: UUID_GENR() for link in template_links}

        # --- STEP 7: Clone project-work-item ---
        new_pwis = []
        for pwi in template_pwis:
            data_pwi = serialize_mapping(pwi)
            data_pwi["_id"] = pwi_id_map[pwi._id]
            data_pwi["project_id"] = project._id
            data_pwi.pop("_created", None)
            data_pwi.pop("_updated", None)
            data_pwi.pop("_etag", None)
            new_pwis.append(data_pwi)
        if new_pwis:
            await self.statemgr.insert_many("project_work_item", *new_pwis)

        # --- STEP 8: Clone project-work-item-deliverable ---
        new_deliverables = []
        for d in template_deliverables:
            data_d = serialize_mapping(d)
            data_d["_id"] = deliverable_id_map[d._id]
            data_d["project_id"] = project._id
            data_d["project_work_item_id"] = pwi_id_map[d.project_work_item_id]
            data_d.pop("_created", None)
            data_d.pop("_updated", None)
            data_d.pop("_etag", None)
            new_deliverables.append(data_d)
        if new_deliverables:
            await self.statemgr.insert_many(
                "project_work_item_deliverable", *new_deliverables
            )

        # --- STEP 9: Clone project-work-package-work-item ---
        new_links = []
        for link in template_links:
            data_l = serialize_mapping(link)
            data_l["_id"] = link_id_map[link._id]
            data_l["project_id"] = project._id
            data_l["project_work_package_id"] = new_pwp_id
            data_l["project_work_item_id"] = pwi_id_map[link.project_work_item_id]
            data_l.pop("_created", None)
            data_l.pop("_updated", None)
            data_l.pop("_etag", None)
            new_links.append(data_l)
        if new_links:
            await self.statemgr.insert_many(
                "project_work_package_work_item", *new_links
            )

        return self.init_resource("project_work_package", pwp_data)

    @action("clone-work-package-deprecated", resources="work_package")
    async def clone_work_package_deprecated(self, /, data):
        """
        Clone a work-package into a project-work-package template (project_id NULL)
        including all related work items and deliverables.
        """
        # --- STEP 1: Lấy work-package ---
        work_package = self.rootobj

        # --- STEP 2: Tạo project-work-package (template) ---
        new_pwp_id = UUID_GENR()
        pwp_data = {
            "_id": new_pwp_id,
            "project_id": None,
            "work_package_id": work_package._id,
            "work_package_name": work_package.work_package_name,
            "work_package_description": work_package.description,
            "work_package_example_description": work_package.example_description,
            "work_package_is_custom": True,
            "work_package_complexity_level": work_package.complexity_level,
            "work_package_estimate": work_package.estimate,
        }
        await self.statemgr.insert(self.init_resource("project_work_package", pwp_data))

        # --- STEP 3: Lấy work-package-work-item ---
        wp_work_items = await self.statemgr.find_all(
            "work_package_work_item", where=dict(work_package_id=work_package._id)
        )
        if not wp_work_items:
            return self.init_resource("project_work_package", pwp_data)

        work_item_ids = [w.work_item_id for w in wp_work_items]
        original_work_items = await self.statemgr.find_all(
            "work_item", where={"_id.in": work_item_ids}
        )
        work_item_lookup = {w._id: w for w in original_work_items}

        # --- STEP 4: Lấy deliverables ---
        all_deliverables = await self.statemgr.find_all(
            "work_item_deliverable", where={"work_item_id.in": work_item_ids}
        )
        deliverables_by_work_item = {}
        for d in all_deliverables:
            deliverables_by_work_item.setdefault(d.work_item_id, []).append(d)

        # --- STEP 5: Chuẩn bị batch insert ---
        project_work_items_batch = []
        project_deliverables_batch = []
        project_wp_work_items_batch = []

        pwi_id_map = {}

        for wp_wi in wp_work_items:
            original_wi = work_item_lookup.get(wp_wi.work_item_id)
            if not original_wi:
                continue

            # Clone project-work-item
            data_pwi = serialize_mapping(original_wi)
            data_pwi.pop("_created", None)
            data_pwi.pop("_updated", None)
            data_pwi.pop("_etag", None)
            data_pwi.pop("organization_id", None)

            new_pwi_id = UUID_GENR()
            data_pwi["_id"] = new_pwi_id
            data_pwi["project_id"] = None
            project_work_items_batch.append(data_pwi)
            pwi_id_map[original_wi._id] = new_pwi_id

            # Clone deliverables
            for d in deliverables_by_work_item.get(wp_wi.work_item_id, []):
                data_d = serialize_mapping(d)
                data_d.pop("_id", None)
                data_d.pop("_created", None)
                data_d.pop("_updated", None)
                data_d.pop("_etag", None)
                data_d.pop("work_item_id", None)
                data_d["_id"] = UUID_GENR()
                data_d["project_id"] = None
                data_d["project_work_item_id"] = new_pwi_id
                project_deliverables_batch.append(data_d)

            # Clone project-work-package-work-item link
            data_link = serialize_mapping(wp_wi)
            data_link.pop("_id", None)
            data_link.pop("_created", None)
            data_link.pop("_updated", None)
            data_link.pop("_etag", None)
            data_link.pop("work_package_id", None)
            data_link.pop("work_item_id", None)
            data_link["_id"] = UUID_GENR()
            data_link["project_id"] = None
            data_link["project_work_package_id"] = new_pwp_id
            data_link["project_work_item_id"] = new_pwi_id
            project_wp_work_items_batch.append(data_link)

        # --- STEP 6: Insert batch ---
        if project_work_items_batch:
            await self.statemgr.insert_many(
                "project_work_item", *project_work_items_batch
            )
        if project_deliverables_batch:
            await self.statemgr.insert_many(
                "project_work_item_deliverable", *project_deliverables_batch
            )
        if project_wp_work_items_batch:
            await self.statemgr.insert_many(
                "project_work_package_work_item", *project_wp_work_items_batch
            )

        return self.init_resource("project_work_package", pwp_data)

    @action("work-package-removed", resources="project")
    async def remove_work_package_from_estimator(self, /, data):
        """Remove a work package and all related items from the project estimator"""
        project = self.rootobj

        project_work_package = await self.statemgr.find_one(
            "project_work_package",
            where=dict(work_package_id=data.work_package_id, project_id=project._id),
        )
        await self.statemgr.invalidate_one(
            "project_work_package", project_work_package._id
        )

    # =========== Project BDM Contact (Project Context) ============

    @action("project-bdm-contact-created", resources="project")
    async def create_project_bdm_contact(self, /, data):
        project = self.rootobj
        """Create a new BDM contact for a project"""
        record = self.init_resource(
            "project_bdm_contact",
            serialize_mapping(data),
            project_id=project._id,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("project-bdm-contact-updated", resources="project")
    async def update_project_bdm_contact(self, /, data):
        project = self.rootobj
        """Update a project BDM contact"""
        record = await self.statemgr.find_one(
            "project_bdm_contact",
            where=dict(project_id=project._id, _id=data.bdm_contact_id),
        )

        if not record:
            raise ValueError("BDM contact not found")

        if data.status:
            workflow_id = await self.statemgr.get_workflow_id("project_bdm_contact")
            to_workflow_status = await self.statemgr.has_workflow_status(
                workflow_id, data.status
            )
            if not to_workflow_status:
                raise ValueError("Invalid status")
            transition = await self.statemgr.has_workflow_transition(
                workflow_id, record.status, data.status
            )
            if not transition:
                raise ValueError("Invalid status, Can not transition to this status")

        update_data = serialize_mapping(data)
        update_data.pop("bdm_contact_id", None)

        await self.statemgr.update(record, **update_data)

    @action("project-bdm-contact-deleted", resources="project")
    async def delete_project_bdm_contact(self, /, data):
        project = self.rootobj
        """Delete a project BDM contact"""
        record = await self.statemgr.find_one(
            "project_bdm_contact",
            where=dict(_id=data.bdm_contact_id, project_id=project._id),
        )

        if not record:
            raise ValueError("BDM contact not found or does not belong to this project")

        await self.statemgr.invalidate(record)

    # =========== Promotion (Promotion Context) ============

    @action("promotion-created", resources="promotion")
    async def create_promotion(self, /, data):
        record = self.init_resource(
            "promotion",
            serialize_mapping(data),
            _id=UUID_GENR(),
            organization_id=self.context.organization_id,
        )
        """Create a new promotion code"""
        await self.statemgr.insert(record)
        return record

    @action("promotion-updated", resources="promotion")
    async def update_promotion(self, /, data):
        promotion = self.rootobj
        await self.statemgr.update(promotion, **serialize_mapping(data))
        return promotion

    @action("promotion-removed", resources="promotion")
    async def remove_promotion(self, /, data):
        """Remove a promotion code"""
        promotion = self.rootobj
        await self.statemgr.invalidate(promotion)
        return promotion

    # =========== Project Member (Project Context) ============

    @action("member-added", resources="project")
    async def add_project_member(self, /, member_id: str, role: str):
        project = self.rootobj

        """Add member to project"""
        record = self.init_resource(
            "project_member",
            {"member_id": member_id, "role": role, "project_id": project._id},
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("member-updated", resources="project")
    async def update_project_member(self, /, data):
        """Update project member"""
        project = self.rootobj
        project_member = await self.statemgr.find_one(
            "project_member",
            where=dict(project_id=project._id, member_id=data.member_id),
        )

        if not project_member:
            raise ValueError("Project member not found")

        await self.statemgr.update(project_member, **serialize_mapping(data))
        return project_member

    @action("member-removed", resources="project")
    async def remove_project_member(self, /, member_id: str):
        """Remove project member"""
        project = self.rootobj
        project_member = await self.statemgr.find_one(
            "project_member", where=dict(project_id=project._id, member_id=member_id)
        )

        if not project_member:
            raise ValueError("Project member not found")

        await self.statemgr.invalidate_one("project_member", project_member._id)

    # =========== Project Milestone (Project Context) ============

    @action("milestone-created", resources="project")
    async def create_project_milestone(self, /, data):
        project = self.rootobj
        project_data = serialize_mapping(data)
        record = self.init_resource(
            "project_milestone", _id=UUID_GENR(), project_id=project._id, **project_data
        )
        await self.statemgr.insert(record)
        return record

    @action("milestone-updated", resources="project")
    async def update_project_milestone(self, /, data):
        """Update project milestone"""
        milestone = await self.statemgr.find_one(
            "project_milestone",
            where=dict(_id=data.milestone_id, project_id=self.aggroot.identifier),
        )

        if not milestone:
            raise ValueError("Milestone not found or does not belong to this project")

        update_data = serialize_mapping(data)
        update_data.pop("milestone_id", None)

        await self.statemgr.update(milestone, **update_data)
        result = await self.statemgr.find_one(
            "project_milestone",
            where=dict(_id=data.milestone_id, project_id=self.aggroot.identifier),
        )
        return result

    @action("milestone-deleted", resources="project")
    async def delete_project_milestone(self, /, data):
        """Delete project milestone"""
        await self.statemgr.invalidate_one("project_milestone", data.milestone_id)

    # =========== Project Category (Project Context) ============
    @action("project-category-created", resources="project")
    async def create_project_category(self, /, data):
        """Create project category"""
        record = self.init_resource(
            "ref__project_category", serialize_mapping(data), _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action("project-category-updated", resources="project")
    async def update_project_category(self, /, data):
        """Update project category"""
        category = await self.statemgr.find_one(
            "ref__project_category", where=dict(_id=data.project_category_id)
        )

        if not category:
            raise ValueError("Category not found")

        update_data = serialize_mapping(data)
        update_data.pop("project_category_id", None)

        await self.statemgr.update(category, **update_data)
        return category

    @action("project-category-deleted", resources="project")
    async def delete_project_category(self, /, data):
        """Delete project category"""
        await self.statemgr.invalidate_one(
            "ref__project_category", data.project_category_id
        )

    # =========== Work Package Context ============

    @action("work-package-created", resources="work_package")
    async def create_work_package(self, /, data):
        """Create new work package"""
        record = self.init_resource(
            "work_package",
            serialize_mapping(data),
            _id=UUID_GENR(),
            organization_id=self.context.organization_id,
        )
        await self.statemgr.insert(record)
        return record

    @action("work-package-updated", resources="work_package")
    async def update_work_package(self, /, data):
        """Update work package details"""
        work_package = self.rootobj
        await self.statemgr.update(work_package, **serialize_mapping(data))
        return work_package

    @action("work-package-invalidated", resources="work_package")
    async def invalidate_work_package(self, /):
        """Invalidate work package"""
        work_package = self.rootobj
        await self.statemgr.invalidate(work_package)
        return work_package

    @action("clone-work-package", resources="work_package")
    async def clone_work_package(self, /, data):
        """
        Clone a work package into a new work package and copy all related work items
        via work-package-work-item.
        """
        original_wp = self.rootobj

        original_wp_items = await self.statemgr.find_all(
            "work_package_work_item", where=dict(work_package_id=original_wp._id)
        )

        new_wp_data = serialize_mapping(original_wp)
        new_wp_data.pop("_id", None)
        new_wp_data.pop("_created", None)
        new_wp_data.pop("_updated", None)
        new_wp_data.pop("_etag", None)

        new_wp_id = UUID_GENR()
        new_wp_data["_id"] = new_wp_id
        new_wp_data["work_package_name"] = f"{original_wp.work_package_name} (Copy)"

        new_wp = self.init_resource(
            "work_package",
            new_wp_data,
            _id=new_wp_id,
            organization_id=self.context.organization_id,
        )
        await self.statemgr.insert(new_wp)

        if not original_wp_items:
            return new_wp

        new_wp_items_batch = []
        for wp_item in original_wp_items:
            wp_item_data = serialize_mapping(wp_item)
            wp_item_data.pop("_id", None)
            wp_item_data.pop("_created", None)
            wp_item_data.pop("_updated", None)
            wp_item_data.pop("_etag", None)
            wp_item_data["work_package_id"] = new_wp_id
            wp_item_data["_id"] = UUID_GENR()
            new_wp_items_batch.append(wp_item_data)

        if new_wp_items_batch:
            await self.statemgr.insert_many(
                "work_package_work_item", *new_wp_items_batch
            )

        return new_wp

    # =========== Work Item Context ============

    @action("work-item-created", resources="work_item")
    async def create_work_item(self, /, data):
        try:
            parsed_estimate = parse_duration_for_db(data.estimate)
            data = data.set(estimate=parsed_estimate)
        except Exception:
            raise ValueError(f"Invalid estimate format: {data.estimate}")

        """Create new work item"""
        record = self.init_resource(
            "work_item",
            serialize_mapping(data),
            _id=UUID_GENR(),
            organization_id=self.context.organization_id,
        )
        await self.statemgr.insert(record)
        return record

    @action("work-item-updated", resources="work_item")
    async def update_work_item(self, /, data):
        """Update work item"""
        work_item = self.rootobj

        if data.estimate:
            try:
                parsed_estimate = parse_duration_for_db(data.estimate)
                data = data.set(estimate=parsed_estimate)
            except Exception:
                raise ValueError(f"Invalid estimate format: {data.estimate}")

        await self.statemgr.update(work_item, **serialize_mapping(data))
        return work_item

    @action("work-item-invalidated", resources="work_item")
    async def invalidate_work_item(self, /, data):
        """Invalidate work item"""
        work_item = self.rootobj
        await self.statemgr.invalidate(work_item)
        return work_item

    # =========== Work Item Deliverable (Work Item Context) ============
    @action("work-item-deliverable-created", resources="work_item")
    async def create_work_item_deliverable(self, /, data):
        """Create new work item deliverable"""
        record = self.init_resource(
            "work_item_deliverable", serialize_mapping(data), _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action("work-item-deliverable-updated", resources="work_item")
    async def update_work_item_deliverable(self, /, data):
        """Update work item deliverable"""
        work_item_deliverable = await self.statemgr.find_one(
            "work_item_deliverable",
            where=dict(
                _id=data.work_item_deliverable_id, work_item_id=self.rootobj._id
            ),
        )
        if not work_item_deliverable:
            raise ValueError("Work item deliverable not found")

        update_data = serialize_mapping(data)
        update_data.pop("work_item_deliverable_id", None)

        result = await self.statemgr.update(work_item_deliverable, **update_data)
        return result

    @action("work-item-deliverable-invalidated", resources="work_item")
    async def invalidate_work_item_deliverable(self, /, data):
        """Invalidate work item deliverable"""
        deliverable = await self.statemgr.find_one(
            "work_item_deliverable",
            where=dict(
                work_item_id=self.rootobj._id, _id=data.work_item_deliverable_id
            ),
        )
        if deliverable:
            await self.statemgr.invalidate_one("work_item_deliverable", deliverable._id)
        else:
            raise ValueError("Work item deliverable not found")

    # =========== Work Item to Work Package (Work Package Context) ============
    @action("work-item-added-to-work-package", resources="work_package")
    async def add_work_item_to_work_package(self, /, work_item_id):
        """Add work item to work package"""
        work_package = self.rootobj
        data = {"work_package_id": work_package._id, "work_item_id": work_item_id}
        record = self.init_resource("work_package_work_item", serialize_mapping(data))
        await self.statemgr.insert(record)
        return record

    @action("work-item-removed-from-work-package", resources="work_package")
    async def remove_work_item_from_work_package(self, /, work_item_id):
        """Remove work item from work package"""
        work_package = self.rootobj
        work_package_work_item = await self.statemgr.find_one(
            "work_package_work_item",
            where=dict(work_package_id=work_package._id, work_item_id=work_item_id),
        )
        if not work_package_work_item:
            raise ValueError("Work item not found")

        await self.statemgr.invalidate_one(
            "work_package_work_item", work_package_work_item._id
        )

    # =========== Work Item Type (Work Item Context) ============

    @action("work-item-type-created", resources="work_item")
    async def create_work_item_type(self, /, data):
        """Create new work item type"""
        record = self.init_resource(
            "ref__work_item_type", serialize_mapping(data), _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action("work-item-type-updated", resources="work_item")
    async def update_work_item_type(self, /, data):
        """Update work item type"""
        work_item_type = await self.statemgr.find_one(
            "ref__work_item_type", where=dict(_id=data.work_item_type_id)
        )

        if not work_item_type:
            raise ValueError("Work item type not found")

        update_data = serialize_mapping(data)
        update_data.pop("work_item_type_id", None)

        await self.statemgr.update(work_item_type, **update_data)
        return work_item_type

    @action("work-item-type-invalidated", resources="work_item")
    async def invalidate_work_item_type(self, /, data):
        """Invalidate work item type"""
        work_item_type = await self.statemgr.find_one(
            "ref__work_item_type", where=dict(_id=data.work_item_type_id)
        )

        if not work_item_type:
            raise ValueError("Work item type not found")

        await self.statemgr.invalidate_one("ref__work_item_type", work_item_type._id)
        return work_item_type

    # =========== Project Work Item (Project Context) ============

    @action("project-work-item-updated", resources="project")
    async def update_project_work_item(self, /, data):
        """Update project work item"""
        project_work_item = await self.statemgr.find_one(
            "project_work_item",
            where=dict(
                _id=data.project_work_item_id, project_id=self.aggroot.identifier
            ),
        )
        if not project_work_item:
            raise ValueError("Project work item not found")

        update_data = serialize_mapping(data)
        update_data.pop("project_work_item_id", None)

        await self.statemgr.update(project_work_item, **update_data)
        return project_work_item

    # =========== Project Work Package (Project Context) ============

    @action("project-work-package-updated", resources="project")
    async def update_project_work_package(self, /, data):
        """Update project work package"""
        project_work_package = await self.statemgr.find_one(
            "project_work_package",
            where=dict(
                _id=data.project_work_package_id, project_id=self.aggroot.identifier
            ),
        )

        if not project_work_package:
            raise ValueError("Project work package not found")

        update_data = serialize_mapping(data)
        update_data.pop("project_work_package_id", None)

        await self.statemgr.update(project_work_package, **update_data)
        return project_work_package

    @action("project-work-package-updated-with-work-items", resources="project")
    async def update_project_work_package_with_work_items(self, /, data):
        """Update project work package and sync work items"""

        project_work_package = await self.statemgr.find_one(
            "project_work_package",
            where=dict(
                _id=data.project_work_package_id, project_id=self.aggroot.identifier
            ),
        )
        if not project_work_package:
            raise ValueError("Project work package not found")

        existing_links = await self.statemgr.find_all(
            "project_work_package_work_item",
            where=dict(project_work_package_id=data.project_work_package_id),
        )
        existing_project_work_item_ids = {
            link.project_work_item_id for link in existing_links
        }
        input_ids = set(data.work_item_ids)  # Convert list to set

        keep_ids = existing_project_work_item_ids & input_ids

        to_remove_ids = existing_project_work_item_ids - keep_ids
        for work_item_id in to_remove_ids:
            link_record = next(
                (
                    link
                    for link in existing_links
                    if link.project_work_item_id == work_item_id
                ),
                None,
            )
            if link_record:
                await self.statemgr.invalidate_one(
                    "project_work_package_work_item", link_record._id
                )
            await self.statemgr.invalidate_one("project_work_item", work_item_id)

        to_add_ids = input_ids - existing_project_work_item_ids

        for work_item_id in to_add_ids:
            work_item = await self.statemgr.find_one(
                "work_item", where=dict(_id=work_item_id)
            )
            if not work_item:
                raise ValueError(f"Work item {work_item_id} not found")

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
                "project_work_item", serialize_mapping(project_work_item_data)
            )
            await self.statemgr.insert(project_work_item)

            link_data = {
                "project_work_package_id": project_work_package._id,
                "project_work_item_id": project_work_item._id,
                "project_id": self.aggroot.identifier,
            }
            link_record = self.init_resource(
                "project_work_package_work_item", serialize_mapping(link_data)
            )
            await self.statemgr.insert(link_record)

        update_data = serialize_mapping(data)
        update_data.pop("project_work_package_id", None)
        update_data.pop("work_item_ids", None)
        await self.statemgr.update(project_work_package, **update_data)

        return project_work_package

    # =========== Project Work Package Work Item (Project Context) ============

    @action("add-new-work-item-to-project-work-package", resources="project")
    async def add_new_work_item_to_project_work_package(self, /, data):
        """Add new work item to project work package and clone into project work item"""

        project_work_package = await self.statemgr.find_one(
            "project_work_package",
            where=dict(
                _id=data.project_work_package_id, project_id=self.aggroot.identifier
            ),
        )
        if not project_work_package:
            raise ValueError("Project work package not found")

        work_item = await self.statemgr.find_one(
            "work_item", where=dict(_id=data.work_item_id)
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
            "project_work_item", serialize_mapping(project_work_item_data)
        )
        await self.statemgr.insert(project_work_item)

        link_data = {
            "project_work_package_id": project_work_package._id,
            "project_work_item_id": project_work_item._id,
            "project_id": self.aggroot.identifier,
        }
        record = self.init_resource(
            "project_work_package_work_item", serialize_mapping(link_data)
        )
        await self.statemgr.insert(record)
        return project_work_item

    @action("remove-project-work-item-from-project-work-package", resources="project")
    async def remove_project_work_item_from_project_work_package(self, /, data):
        """Remove project work item from project work package"""
        project_work_item = await self.statemgr.find_one(
            "project_work_item",
            where=dict(
                _id=data.project_work_item_id, project_id=self.aggroot.identifier
            ),
        )
        if not project_work_item:
            raise ValueError("Project work item not found")

        await self.statemgr.invalidate_one("project_work_item", project_work_item._id)

    # =========== Project Work Item Deliverable (Project Context) ============

    @action("project-work-item-deliverable-updated", resources="project")
    async def update_project_work_item_deliverable(self, /, data):
        """Update project work item deliverable"""
        project_work_item_deliverable = await self.statemgr.find_one(
            "project_work_item_deliverable",
            where=dict(
                _id=data.project_work_item_deliverable_id,
                project_id=self.aggroot.identifier,
            ),
        )

        if not project_work_item_deliverable:
            raise ValueError("Project work item deliverable not found")

        update_data = serialize_mapping(data)
        update_data.pop("project_work_item_deliverable_id", None)

        await self.statemgr.update(project_work_item_deliverable, **update_data)
        return project_work_item_deliverable

    @action("project-integration-created", resources="project")
    async def create_project_integration(self, /, data):
        """Create a project integration"""
        project_integration = self.init_resource(
            "project_integration",
            serialize_mapping(data),
            project_id=self.aggroot.identifier,
        )
        await self.statemgr.insert(project_integration)
        return project_integration

    @action("project-integration-updated", resources="project")
    async def update_project_integration(self, /, data):
        """Update a project integration"""
        project = self.rootobj
        logger.info(f"Update project: {project}")
        project_integration = await self.statemgr.find_one(
            "project_integration",
            where=dict(
                provider=data.provider,
                external_id=data.external_id,
                project_id=project._id,
            ),
        )
        if not project_integration:
            raise ValueError("Project integration not found")
        await self.statemgr.update(project_integration)

    @action("project-integration-removed", resources="project")
    async def remove_project_integration(self, /, data):
        """Delete a project integration"""
        # project = self.rootobj
        # logger.info(f"Delete project: {project}")
        project_integration = await self.statemgr.find_one(
            "project_integration",
            where=dict(
                provider=data.provider,
                external_id=data.external_id,
                # project_id=project._id
            ),
        )

        if not project_integration:
            raise ValueError("Project integration not found")
        await self.statemgr.invalidate_one(
            "project_integration", project_integration._id
        )

    @action("sync-project-integration", resources="project")
    async def sync_project_integration(self, /, data):
        """Sync a project integration"""
        project_integration = await self.statemgr.find_one(
            "project_integration",
            where=dict(
                provider=data.provider,
                external_id=data.external_id,
                project_id=self.aggroot.identifier,
            ),
        )

        logger.info(f"Project integration: {project_integration}")
        if not project_integration:
            project_integration = self.init_resource(
                "project_integration",
                serialize_mapping(data),
                project_id=self.aggroot.identifier,
            )
            await self.statemgr.insert(project_integration)
        else:
            update_data = serialize_mapping(data)
            await self.statemgr.update(project_integration, **update_data)
        return project_integration

    ### Action Project Milestone Integration

    @action("create-project-milestone-integration", resources="project")
    async def create_project_milestone_integration(self, /, data):
        """create a project milestone integration"""
        milestone = await self.statemgr.find_one(
            "project_milestone",
            where=dict(_id=data.milestone_id, project_id=self.aggroot.identifier),
        )

        if not milestone:
            raise ValueError("Milestone not found or does not belong to this project")

        project_milestone_integration = self.init_resource(
            "project_milestone_integration",
            serialize_mapping(data),
        )
        await self.statemgr.insert(project_milestone_integration)
        return project_milestone_integration

    @action("update-project-milestone-integration", resources="project")
    async def update_project_milestone_integration(self, /, data):
        """update project milestone integration"""
        milestone = await self.statemgr.find_one(
            "project_milestone",
            where=dict(_id=data.milestone_id, project_id=self.aggroot.identifier),
        )

        if not milestone:
            raise ValueError("Milestone not found or does not belong to this project")

        project_milestone_integration = await self.statemgr.find_one(
            "project_milestone_integration",
            where=dict(
                milestone_id=data.milestone_id,
                provider=data.provider,
                external_id=data.external_id,
            ),
        )
        if not project_milestone_integration:
            raise ValueError("Project milestone integration not found")
        update_data = serialize_mapping(data)
        await self.statemgr.update(project_milestone_integration, **update_data)

    @action("remove-project-milestone-integration", resources="project")
    async def remove_project_milestone_integration(self, /, data):
        """remove project milestone integration"""
        project_milestone_integration = await self.statemgr.find_one(
            "project_milestone_integration",
            where=dict(
                milestone_id=data.milestone_id,
                provider=data.provider,
                external_id=data.external_id,
            ),
        )
        if not project_milestone_integration:
            raise ValueError("Project milestone integration not found")
        await self.statemgr.invalidate_one(
            "project_milestone_integration", project_milestone_integration._id
        )

    @action("ticket-type-created", resources="ticket")
    async def create_ticket_type(self, /, data):
        """Create a new ticket type"""
        record = self.init_resource(
            "ref__ticket_type", serialize_mapping(data), _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action("ticket-type-updated", resources="ticket")
    async def update_ticket_type(self, /, data):
        """Update a ticket type"""
        ticket_type = await self.statemgr.find_one(
            "ref__ticket_type", where=dict(_id=data.ticket_type_id)
        )
        if not ticket_type:
            raise ValueError("Ticket type not found")
        updated_data = serialize_mapping(data)
        updated_data.pop("ticket_type_id")
        await self.statemgr.update(ticket_type, **updated_data)
        return ticket_type

    @action("ticket-type-deleted", resources="ticket")
    async def delete_ticket_type(self, /, data):
        """Delete a ticket type"""
        ticket_type = await self.statemgr.find_one(
            "ref__ticket_type", where=dict(_id=data.ticket_type_id)
        )
        if not ticket_type:
            raise ValueError("Ticket type not found")
        await self.statemgr.invalidate_one("ref__ticket_type", data.ticket_type_id)
        return {"deleted": True}

    # =========== Inquiry (Ticket Context) ============

    @action("inquiry-created", resources="ticket")
    async def create_inquiry(self, /, data):
        """Create a new inquiry"""

        record = self.init_resource(
            "ticket",
            serialize_mapping(data),
            status=InquiryStatusEnum.OPEN.value,
            organization_id=self.context.organization_id,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("inquiry-draft-created", resources="ticket")
    async def create_inquiry_draft(self, /, data):
        """Create a new inquiry draft"""

        record = self.init_resource(
            "ticket",
            serialize_mapping(data),
            status=InquiryStatusEnum.DRAFT.value,
            organization_id=self.context.organization_id,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("close-inquiry", resources="ticket")
    async def close_inquiry(self, /):
        """close inquiry ticket"""
        inquiry = self.rootobj
        if not inquiry:
            raise ValueError("Inquiry not found")
        if inquiry.status == InquiryStatusEnum.CLOSED.value:
            raise ValueError("Inquiry is already closed")
        if inquiry.status == InquiryStatusEnum.DRAFT.value:
            raise ValueError("Draft inquiry cannot be closed")
        await self.statemgr.update(inquiry, status=InquiryStatusEnum.CLOSED.value)
        result = await self.statemgr.find_one(
            "ticket",
            where=dict(_id=inquiry._id),
        )
        return result

    @action("submit-inquiry-draft", resources="ticket")
    async def submit_inquiry_draft(self, /):
        """submit inquiry draft ticket"""
        inquiry = self.rootobj
        if not inquiry:
            raise ValueError("Inquiry not found")
        if inquiry.status != InquiryStatusEnum.DRAFT.value:
            raise ValueError("Only draft inquiry can be submitted")
        await self.statemgr.update(inquiry, status=InquiryStatusEnum.OPEN.value)
        result = await self.statemgr.find_one(
            "ticket",
            where=dict(_id=inquiry._id),
        )
        return result

    # =========== Ticket (Ticket Context) ============
    @action("ticket-created", resources="ticket")
    async def create_ticket(self, /, data):
        """Create a new ticket tied to project"""
        data_result = serialize_mapping(data)
        data_result.pop("project_id", None)
        if "organization_id" not in data_result:
            data_result["organization_id"] = self.context.organization_id

        final_kwargs = self.audit_created()
        final_kwargs.update(
            {
                "_id": self.aggroot.identifier,
                "status": "NEW",
                "sync_status": "PENDING",
                "is_inquiry": False,
            }
        )
        final_kwargs.update(data_result)
        record = self.statemgr.create("ticket", None, **final_kwargs)
        await self.statemgr.insert(record)
        return record

    @action("ticket-updated", resources="ticket")
    async def update_ticket_info(self, /, data):
        """Update ticket information"""
        ticket = self.rootobj

        if data.status:
            status = await self.statemgr.find_one(
                "status",
                where=dict(
                    entity_type="ticket",
                ),
            )

            from_status_key = await self.statemgr.find_one(
                "status_key", where=dict(status_id=status._id, key=ticket.status)
            )
            to_status_key = await self.statemgr.find_one(
                "status_key", where=dict(status_id=status._id, key=data.status)
            )

            if not to_status_key:
                raise ValueError("Invalid status")

            transition = await self.statemgr.has_status_transition(
                status._id, from_status_key._id, to_status_key._id
            )
            if not transition:
                raise ValueError("Invalid status, Can not transition to this status")

        data_result = serialize_mapping(data)

        await self.statemgr.update(ticket, **data_result)

    @action("ticket-removed", resources="ticket")
    async def remove_ticket(self, /):
        """Remove ticket"""
        ticket = self.rootobj
        # if not ticket.is_inquiry:
        #     raise ValueError(
        #         "You cannot remove a ticket that attached to a project")
        await self.statemgr.invalidate(ticket)

    # =========== Ticket Assignee (Ticket Context) ============

    @action("member-assigned-to-ticket", resources="ticket")
    async def assign_member_to_ticket(self, /, data):
        """Assign member to ticket"""
        ticket_assignee = await self.statemgr.find_one(
            "ticket_assignee", where=dict(ticket_id=self.aggroot.identifier)
        )
        if ticket_assignee and ticket_assignee.member_id == data.member_id:
            raise ValueError("Member already assigned to ticket")

        if ticket_assignee:
            await self.statemgr.invalidate_one("ticket_assignee", ticket_assignee._id)

        record = self.init_resource(
            "ticket_assignee",
            {"ticket_id": self.aggroot.identifier, "member_id": data.member_id},
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("member-removed-from-ticket", resources="ticket")
    async def remove_member_from_ticket(self, /, member_id: str):
        """Remove member from ticket"""
        assignee = await self.statemgr.find_one(
            "ticket_assignee",
            where=dict(ticket_id=self.aggroot.identifier, member_id=member_id),
        )
        if not assignee:
            raise ValueError("Assignee not found")
        await self.statemgr.invalidate_one("ticket_assignee", assignee._id)
        return {"removed": True}

    # =========== Ticket Participant (Ticket Context) ============

    @action("participant-added-to-ticket", resources="ticket")
    async def add_ticket_participant(self, /, participant_id: str):
        """Add participant to ticket"""
        ticket_participant = await self.statemgr.find_one(
            "ticket_participant",
            where=dict(
                ticket_id=self.aggroot.identifier, participant_id=participant_id
            ),
        )
        if ticket_participant:
            raise ValueError("Participant already added to ticket")

        record = self.init_resource(
            "ticket_participant",
            {"ticket_id": self.aggroot.identifier, "participant_id": participant_id},
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("participant-removed-from-ticket", resources="ticket")
    async def remove_ticket_participant(self, /, participant_id: str):
        """Remove participant from ticket"""
        participant = await self.statemgr.find_one(
            "ticket_participant",
            where=dict(
                ticket_id=self.aggroot.identifier, participant_id=participant_id
            ),
        )
        if not participant:
            raise ValueError("Participant not found")
        await self.statemgr.invalidate_one("ticket_participant", participant._id)
        return {"removed": True}

    # =========== Ticket Tag (Ticket Context) ============
    @action("tag-added-to-ticket", resources="ticket")
    async def add_ticket_tag(self, /, tag_id: str):
        """Add tag to ticket"""
        record = self.init_resource(
            "ticket_tag",
            {"ticket_id": self.aggroot.identifier, "tag_id": tag_id},
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("tag-removed-from-ticket", resources="ticket")
    async def remove_ticket_tag(self, /, tag_id: str):
        """Remove tag from ticket"""
        tags = await self.statemgr.find_all(
            "ticket_tag", where=dict(ticket_id=self.aggroot.identifier, tag_id=tag_id)
        )
        for tag in tags:
            await self.statemgr.invalidate_one("ticket_tag", tag._id)
        return {"removed": True}

    # =========== Tag Context ============
    @action("tag-created", resources="tag")
    async def create_tag(self, /, data):
        """Create a new tag"""
        record = self.init_resource(
            "tag",
            serialize_mapping(data),
            organization_id=self.context.organization_id,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("tag-updated", resources="tag")
    async def update_tag(self, /, data):
        """Update tag"""
        tag = self.rootobj
        await self.statemgr.update(tag, **serialize_mapping(data))
        return tag

    @action("tag-deleted", resources="tag")
    async def delete_tag(self, /):
        """Delete tag"""
        tag = self.rootobj
        if not tag:
            raise ValueError("Tag not found")
        await self.statemgr.invalidate(tag)
        return {"deleted": True}

    @action("status-created", resources="status")
    async def create_status(self, /, data):
        """Create a new workflow"""
        record = self.init_resource("status", serialize_mapping(data), _id=UUID_GENR())
        await self.statemgr.insert(record)
        return record

    @action("status-key-created", resources="status")
    async def create_status_key(self, /, data):
        """Create a new status key"""
        status = self.rootobj
        record = self.init_resource(
            "status_key", serialize_mapping(data), status_id=status._id, _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action("status-transition-created", resources="status")
    async def create_status_transition(self, /, data):
        """Create a new status transition"""
        status = self.rootobj
        record = self.init_resource(
            "status_transition",
            serialize_mapping(data),
            status_id=status._id,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    # ----------- Agg Ticket Integration (Ticket Context) -----------
    @action("create-ticket-integration", resources="ticket")
    async def create_ticket_integration(self, /, data):
        """Create a new ticket integration"""
        ticket = await self.statemgr.find_one(
            "ticket", where=dict(_id=self.aggroot.identifier)
        )
        if not ticket:
            raise ValueError("Ticket not found")

        record = self.init_resource(
            "ticket_integration",
            serialize_mapping(data),
            ticket_id=self.aggroot.identifier,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)

    @action("update-ticket-integration", resources="ticket")
    async def update_ticket_integration(self, /, data):
        """Update ticket integration"""
        ticket = await self.statemgr.find_one(
            "ticket", where=dict(_id=self.aggroot.identifier)
        )
        if not ticket:
            raise ValueError("Ticket not found")
        ticket_integration = await self.statemgr.find_one(
            "ticket_integration",
            where=dict(
                provider=data.provider,
                ticket_id=self.aggroot.identifier,
                external_id=data.external_id,
            ),
        )
        if not ticket_integration:
            raise ValueError("Ticket integration not found")
        await self.statemgr.update(ticket_integration, **serialize_mapping(data))

    @action("remove-ticket-integration", resources="ticket")
    async def remove_ticket_integration(self, /, data):
        """Remove ticket integration"""
        ticket = await self.statemgr.find_one(
            "ticket", where=dict(_id=self.aggroot.identifier)
        )
        if not ticket:
            raise ValueError("Ticket not found")
        ticket_integration = await self.statemgr.find_one(
            "ticket_integration",
            where=dict(
                provider=data.provider,
                ticket_id=self.aggroot.identifier,
                external_id=data.external_id,
            ),
        )
        if not ticket_integration:
            raise ValueError("Ticket integration not found")

        await self.statemgr.invalidate(ticket_integration)
        return {"removed": True}

    @action("comment-created", resources=tuple(config.COMMENT_AGGROOTS.split(",")))
    async def create_comment(self, /, data):
        """Create a new comment"""
        if self.aggroot.resource == "ticket":
            ticket = self.rootobj
            if not ticket:
                raise ValueError("Ticket not found")
            if (
                ticket.is_inquiry and ticket.status == InquiryStatusEnum.OPEN.value
                # and self.get_context().profile_id != ticket._creator
            ):
                await self.statemgr.update(
                    ticket, status=InquiryStatusEnum.DISCUSSION.value
                )

        payload = serialize_mapping(data)
        if "organization_id" not in payload:
            payload["organization_id"] = self.context.organization_id
        final_kwargs = self.audit_created()
        final_kwargs.update(
            {
                "_id": UUID_GENR(),
            }
        )
        final_kwargs.update(payload)
        record = self.statemgr.create(
            "comment",
            None,
            **final_kwargs,
        )
        await self.statemgr.insert(record)

        return record

    @action("comment-updated", resources="comment")
    async def update_comment(self, /, data):
        """Update comment"""
        data_result = serialize_mapping(data)
        await self.statemgr.update(self.rootobj, **data_result)

    @action("comment-deleted", resources="comment")
    async def delete_comment(self, /):
        """Delete comment"""
        comment = self.rootobj
        await self.statemgr.invalidate(comment)

    @action("reply-to-comment", resources="comment")
    async def reply_to_comment(self, /, data):
        """Reply to comment"""
        parent_comment = self.rootobj
        organization_id = self.get_context().organization_id

        logger.info(f"Creating reply to comment: {parent_comment._id}")

        parent_id = parent_comment._id
        depth = parent_comment.depth + 1

        if parent_comment.depth >= config.COMMENT_NESTED_LEVEL:
            depth = parent_comment.depth
            parent_id = parent_comment.parent_id
            logger.info(f"Max nest level reached, attaching to parent: {parent_id}")

        reply_data = serialize_mapping(data)
        reply_data.update(
            {
                "parent_id": parent_id,
                "depth": depth,
                "resource": parent_comment.resource,
                "resource_id": parent_comment.resource_id,
            }
        )

        new_comment = self.init_resource(
            "comment", reply_data, _id=UUID_GENR(), organization_id=organization_id
        )

        await self.statemgr.insert(new_comment)
        return new_comment

    # comment integration

    @action(
        "create-comment-integration",
        resources=tuple(config.COMMENT_AGGROOTS.split(",")),
    )
    async def create_comment_integration(self, /, data):
        """Create a new comment integration"""
        comment = await self.statemgr.find_one(
            "comment", where=dict(_id=data.comment_id)
        )
        if not comment:
            raise ValueError("Comment not found")

        record = self.init_resource(
            "comment_integration",
            serialize_mapping(data),
            # comment_id=self.aggroot.identifier,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("update-comment-integration", resources="comment")
    async def update_comment_integration(self, /, data):
        """Update comment integration"""
        comment = await self.statemgr.find_one(
            "comment", where=dict(_id=self.aggroot.identifier)
        )
        if not comment:
            raise ValueError("Comment not found")

        comment_integration = await self.statemgr.find_one(
            "comment_integration",
            where=dict(
                provider=data.provider,
                comment_id=self.aggroot.identifier,
                external_id=data.external_id,
            ),
        )

        if not comment_integration:
            raise ValueError("Comment integration not found")
        await self.statemgr.update(comment_integration, **serialize_mapping(data))
        return comment_integration

    @action("remove-comment-integration", resources="comment")
    async def remove_comment_integration(self, /, data):
        """Remove comment integration"""
        logger.warn(f"Attempting to remove integration with payload: {data}")
        comment_integration = await self.statemgr.find_one(
            "comment_integration",
            where=dict(
                provider=data.provider,
                comment_id=data.comment_id,
                external_id=data.external_id,
            ),
        )

        if not comment_integration:
            raise ValueError("Comment integration not found")

        await self.statemgr.invalidate(comment_integration)
        return {"removed": True}

    @action("comment-created", resources=tuple(config.COMMENT_AGGROOTS.split(",")))
    async def create_comment_from_webhook(self, /, data):
        """Create a new comment"""
        payload = serialize_mapping(data)
        if "organization_id" not in payload:
            payload["organization_id"] = self.context.organization_id
        final_kwargs = self.audit_created()
        final_kwargs.update(
            {
                "_id": self.aggroot.identifier,
            }
        )
        final_kwargs.update(payload)
        record = self.statemgr.create(
            "comment",
            None,
            **final_kwargs,
        )
        await self.statemgr.insert(record)

        return record

    @action("attach-file", resources="comment")
    async def attach_file_to_comment(self, /, data):
        """Attach file to comment"""
        comment = self.rootobj
        attachment_data = serialize_mapping(data)
        attachment_data["comment_id"] = comment._id
        attachment = self.init_resource(
            "comment_attachment",
            attachment_data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(attachment)
        return attachment

    @action("update-attachment", resources="comment")
    async def update_attachment(self, /, data):
        """Update attachment metadata"""
        comment = self.rootobj
        if not comment:
            raise ValueError("Comment not found")

        attachment = await self.statemgr.find_one(
            "comment_attachment",
            where={"_id": data.attachment_id, "comment_id": comment._id},
        )
        if not attachment:
            raise ValueError(f"Attachment not found: {data.attachment_id}")
        data_result = serialize_mapping(data)
        data_result.pop("attachment_id", None)
        await self.statemgr.update(attachment, **data_result)

    @action("delete-attachment", resources="comment")
    async def delete_attachment(self, /, data):
        """Delete attachment from comment"""
        comment = self.rootobj
        if not comment:
            raise ValueError("Comment not found")
        attachment = await self.statemgr.find_one(
            "comment_attachment",
            where={"_id": data.attachment_id, "comment_id": comment._id},
        )
        if not attachment:
            raise ValueError(f"Attachment not found: {data.attachment_id}")
        await self.statemgr.invalidate(attachment)

    @action("create-reaction-to-comment", resources="comment")
    async def create_reaction_comment(self, /, data):
        """Create reaction to comment"""
        comment = self.rootobj
        user_id = self.get_context().profile_id
        reaction_data = serialize_mapping(data)
        reaction_data.update(
            {
                "comment_id": comment._id,
                "user_id": user_id,
            }
        )
        check_existing = await self.statemgr.find_one(
            "comment_reaction",
            where={
                "comment_id": self.rootobj._id,
                "user_id": user_id,
            },
        )
        if check_existing:
            raise ValueError(
                f"Reaction already exists for user: {user_id} on comment {comment._id}"
            )
        reaction = self.init_resource(
            "comment_reaction",
            reaction_data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(reaction)
        return reaction

    @action("remove-reaction-from-commnent", resources="comment")
    async def remove_reaction(self, /):
        """Remove reaction from comment"""
        user_id = self.get_context().profile_id
        reaction = await self.statemgr.find_one(
            "comment_reaction",
            where={
                "comment_id": self.rootobj._id,
                "user_id": user_id,
            },
        )
        if not reaction:
            raise ValueError(
                f"Reaction not found for user: {user_id} on comment {self.rootobj._id}"
            )
        await self.statemgr.invalidate(reaction)

    @action("document-uploaded", resources="document")
    async def upload_document(self, /, data):
        """Upload a global organization document"""
        document = self.init_resource(
            "document",
            serialize_mapping(data),
            _id=self.aggroot.identifier,
            organization_id=self.context.organization_id,
        )
        await self.statemgr.insert(document)
        return document

    @action("document-updated", resources="document")
    async def update_document(self, /, data):
        """Update document information"""
        document = self.rootobj
        update_data = serialize_mapping(data)
        await self.statemgr.update(document, **update_data)
        return document

    @action("document-deleted", resources="document")
    async def delete_document(self, /):
        """Delete document"""
        document = self.rootobj
        await self.statemgr.invalidate(document)

    @action("participant-added-to-global-document", resources="document")
    async def add_participant_document(self, /, data):
        """Add participant to global organization document"""
        document = self.rootobj

        for participant_id in data.participant_ids:
            existing_participant = await self.statemgr.find_one(
                "document_participant",
                where=dict(
                    document_id=document._id,
                    participant_id=participant_id,
                ),
            )
            if existing_participant:
                continue

            record = self.init_resource(
                "document_participant",
                {
                    "document_id": document._id,
                    "participant_id": participant_id,
                    "role": data.role if hasattr(data, "role") else "REVIEWER",
                    "organization_id": self.context.organization_id,
                },
                _id=UUID_GENR(),
            )
            await self.statemgr.insert(record)
