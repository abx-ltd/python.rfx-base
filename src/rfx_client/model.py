import array
import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg


from . import types, config


class CPOPortalConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_client.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class CPOPortalBaseModel(CPOPortalConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {'schema': config.CPO_PORTAL_SCHEMA}

    _realm = sa.Column(sa.String)

# ================ Promotion Context ================


class Promotion(CPOPortalBaseModel):
    __tablename__ = "promotion"

    code = sa.Column(sa.String(50), nullable=False, unique=True)
    valid_from = sa.Column(sa.DateTime(timezone=True), nullable=False)
    valid_until = sa.Column(sa.DateTime(timezone=True), nullable=False)
    max_uses = sa.Column(sa.Integer, nullable=False)
    current_uses = sa.Column(sa.Integer, default=0)
    discount_value = sa.Column(sa.Numeric(10, 2), nullable=False)


# ================ Project Context ================
# Project Aggregate Root
class Project(CPOPortalBaseModel):
    __tablename__ = "project"

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    category = sa.Column(sa.String(100))  # FK to ref--project-category
    priority = sa.Column(
        sa.Enum(types.Priority, name="priority",
                schema=config.CPO_PORTAL_SCHEMA),
        nullable=False
    )
    status = sa.Column(sa.String(100), nullable=False)
    start_date = sa.Column(sa.DateTime(timezone=True))
    target_date = sa.Column(sa.DateTime(timezone=True))
    duration = sa.Column(sa.Interval)
    free_credit_applied = sa.Column(sa.Integer, default=0)
    lead_id = sa.Column(pg.UUID)  # FK to profile(_id)
    referral_code_used = sa.Column(sa.String(50))
    status_workflow_id = sa.Column(pg.UUID)  # FK to workflow(_id)
    sync_status = sa.Column(
        sa.Enum(types.SyncStatus, name="sync_status",
                schema=config.CPO_PORTAL_SCHEMA),
        default=types.SyncStatus.PENDING
    )


class ViewProject(CPOPortalBaseModel):
    __tablename__ = "_project"

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    category = sa.Column(sa.String(100))  # FK to ref--project-category
    priority = sa.Column(
        sa.Enum(types.Priority, name="priority",
                schema=config.CPO_PORTAL_SCHEMA),
        nullable=False
    )
    status = sa.Column(sa.String(100), nullable=False)
    start_date = sa.Column(sa.DateTime(timezone=True))
    target_date = sa.Column(sa.DateTime(timezone=True))
    duration = sa.Column(sa.Interval)
    free_credit_applied = sa.Column(sa.Integer, default=0)
    lead_id = sa.Column(pg.UUID)  # FK to profile(_id)
    referral_code_used = sa.Column(sa.String(50))
    status_workflow_id = sa.Column(pg.UUID)  # FK to workflow(_id)
    sync_status = sa.Column(
        sa.Enum(types.SyncStatus, name="sync_status",
                schema=config.CPO_PORTAL_SCHEMA),
        default=types.SyncStatus.PENDING
    )
    members = sa.Column(pg.ARRAY(pg.UUID))

# Project Resource Entity


class ProjectResource(CPOPortalBaseModel):
    __tablename__ = "project-resource"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    resource_id = sa.Column(pg.UUID, nullable=False)  # FK to resource(_id)
    # 'file', 'link', etc.
    resource_type = sa.Column(sa.String(100), nullable=False)
    filename = sa.Column(sa.String(255))
    file_size = sa.Column(sa.Integer)
    mime_type = sa.Column(sa.String(100))
    url = sa.Column(sa.String(500))


# Project Milestone Entity
class ProjectMilestone(CPOPortalBaseModel):
    __tablename__ = "project-milestone"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    due_date = sa.Column(sa.DateTime(timezone=True), nullable=False)
    completed_at = sa.Column(sa.DateTime(timezone=True))
    is_completed = sa.Column(sa.Boolean, default=False)


# Project Ticket Entity
class ProjectTicket(CPOPortalBaseModel):
    __tablename__ = "project-ticket"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    ticket_id = sa.Column(pg.UUID, nullable=False)  # FK to ticket(_id)


# Project Status Entity
class ProjectStatus(CPOPortalBaseModel):
    __tablename__ = "project-status"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    # FK to workflow-status
    src_state = sa.Column(sa.String(100), nullable=False)
    # FK to workflow-status
    dst_state = sa.Column(sa.String(100), nullable=False)
    note = sa.Column(sa.Text)


# Project Member Entity
class ProjectMember(CPOPortalBaseModel):
    __tablename__ = "project-member"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    member_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)
    role = sa.Column(sa.String(100), nullable=False)  # FK to ref--project-role
    permission = sa.Column(sa.String(255))


# Project Work Package Entity
class ProjectWorkPackage(CPOPortalBaseModel):
    __tablename__ = "project-work-package"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    # FK to work_package(_id)
    work_package_id = sa.Column(pg.UUID, nullable=False)
    quantity = sa.Column(sa.Integer, nullable=False, default=1)
    work_package_name = sa.Column(sa.String(255), nullable=False)
    work_package_description = sa.Column(sa.Text)
    work_package_example_description = sa.Column(sa.Text)
    work_package_is_custom = sa.Column(sa.Boolean, default=False)
    work_package_complexity_level = sa.Column(sa.Integer, default=1)
    work_package_estimate = sa.Column(sa.Interval)


class ProjectWorkItem(CPOPortalBaseModel):
    __tablename__ = "project-work-item"
    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2))
    credit_per_unit = sa.Column(sa.Numeric(10, 2))
    estimate = sa.Column(sa.Interval)
    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)


class ProjectWorkPackageWorkItem(CPOPortalBaseModel):
    __tablename__ = "project-work-package-work-item"
    project_work_package_id = sa.Column(
        sa.ForeignKey(ProjectWorkPackage._id), nullable=False)
    project_work_item_id = sa.Column(sa.ForeignKey(
        ProjectWorkItem._id), nullable=False)
    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)


class ProjectWorkItemDeliverable(CPOPortalBaseModel):
    __tablename__ = "project-work-item-deliverable"
    project_work_item_id = sa.Column(sa.ForeignKey(
        ProjectWorkItem._id), nullable=False)
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.Text)
    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)


class ViewProjectWorkPackage(CPOPortalBaseModel):
    __tablename__ = "_project-work-package"
    __table_args__ = {'schema': config.CPO_PORTAL_SCHEMA}

    project_id = sa.Column(pg.UUID, primary_key=True)
    work_package_id = sa.Column(pg.UUID, primary_key=True)
    work_package_name = sa.Column(sa.String(255), nullable=False)
    work_package_description = sa.Column(sa.Text)
    work_package_example_description = sa.Column(sa.Text)
    work_package_complexity_level = sa.Column(sa.Integer, nullable=False)
    work_package_estimate = sa.Column(sa.Interval)
    work_package_is_custom = sa.Column(sa.Boolean, default=False)
    status = sa.Column(sa.String(100), nullable=False)
    quantity = sa.Column(sa.Integer, nullable=False)
    type_list = sa.Column(pg.ARRAY(sa.String))
    work_item_count = sa.Column(sa.Integer, nullable=False)
    credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    architectural_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    development_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    operation_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    upfront_cost = sa.Column(sa.Numeric(10, 2), nullable=False)
    monthly_cost = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_deliverables = sa.Column(sa.Integer, nullable=False)


class ViewProjectWorkItem(CPOPortalBaseModel):
    __tablename__ = "_project-work-item"
    __table_args__ = {'schema': config.CPO_PORTAL_SCHEMA}

    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)
    type_alias = sa.Column(sa.String(50), nullable=False)


class ViewProjectWorkItemListing(CPOPortalBaseModel):
    __tablename__ = "_project-work-item-listing"
    __table_args__ = {'schema': config.CPO_PORTAL_SCHEMA}

    project_work_package_id = sa.Column(pg.UUID, primary_key=True)
    project_work_item_id = sa.Column(pg.UUID, primary_key=True)
    project_work_item_name = sa.Column(sa.String(255), nullable=False)
    project_work_item_description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    project_work_item_type_code = sa.Column(sa.String(100), nullable=False)
    project_work_item_type_alias = sa.Column(sa.String(50), nullable=False)
    total_credits_for_item = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimated_cost_for_item = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)


# Project BDM Contact Entity


class ProjectBDMContact(CPOPortalBaseModel):
    __tablename__ = "project-bdm-contact"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    contact_method = sa.Column(pg.ARRAY(sa.Enum(types.ContactMethod, name="contact_method",
                                                schema=config.CPO_PORTAL_SCHEMA)), nullable=False)
    message = sa.Column(sa.Text)
    meeting_time = sa.Column(sa.DateTime(timezone=True))
    status = sa.Column(sa.String(100), nullable=False)
    status_workflow_id = sa.Column(pg.UUID)  # FK to workflow(_id)


class ViewProjectEstimateSummary(CPOPortalBaseModel):
    __tablename__ = "_project-estimate-summary"
    __table_args__ = {'schema': config.CPO_PORTAL_SCHEMA}

    project_id = sa.Column(pg.UUID, primary_key=True)
    architectural_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    development_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    operation_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    discount_value = sa.Column(sa.Numeric(10, 2), nullable=False)
    free_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_credits_raw = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_credits_after_discount = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_cost = sa.Column(sa.Numeric(10, 2), nullable=False)


# Reference Tables


class RefProjectCategory(CPOPortalBaseModel):
    __tablename__ = "ref--project-category"

    key = sa.Column(sa.String(50), nullable=False,
                    unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)


class RefProjectRole(CPOPortalBaseModel):
    __tablename__ = "ref--project-role"

    key = sa.Column(sa.String(50), nullable=False,
                    unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_default = sa.Column(sa.Boolean, default=False)


# ================ Work Item Context ================
class WorkItem(CPOPortalBaseModel):
    __tablename__ = "work-item"

    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)


class RefWorkItemType(CPOPortalBaseModel):
    __tablename__ = "ref--work-item-type"
    key = sa.Column(sa.String(50), nullable=False,
                    unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    alias = sa.Column(sa.String(50))


class WorkItemDeliverable(CPOPortalBaseModel):
    __tablename__ = "work-item-deliverable"

    work_item_id = sa.Column(sa.ForeignKey(WorkItem._id), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)


class ViewWorkItem(CPOPortalBaseModel):
    __tablename__ = "_work-item"
    __table_args__ = {'schema': config.CPO_PORTAL_SCHEMA}

    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)
    type_alias = sa.Column(sa.String(50), nullable=False)


class ViewWorkItemListing(CPOPortalBaseModel):
    __tablename__ = "_work-item-listing"
    __table_args__ = {'schema': config.CPO_PORTAL_SCHEMA}

    work_package_id = sa.Column(pg.UUID, primary_key=True)
    work_item_id = sa.Column(pg.UUID, primary_key=True)
    work_item_name = sa.Column(sa.String(255), nullable=False)
    work_item_description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    work_item_type_code = sa.Column(sa.String(100), nullable=False)
    work_item_type_alias = sa.Column(sa.String(50), nullable=False)
    total_credits_for_item = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimated_cost_for_item = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)


# ================ Work Package Context ================
# Work Package Aggregate Root


class WorkPackage(CPOPortalBaseModel):
    __tablename__ = "work-package"

    work_package_name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    example_description = sa.Column(sa.Text)
    is_custom = sa.Column(sa.Boolean, default=False)
    complexity_level = sa.Column(sa.Integer, default=1)
    estimate = sa.Column(sa.Interval)


class WorkPackageWorkItem(CPOPortalBaseModel):
    __tablename__ = "work-package-work-item"

    work_package_id = sa.Column(sa.ForeignKey(WorkPackage._id), nullable=False)
    work_item_id = sa.Column(sa.ForeignKey(WorkItem._id), nullable=False)


class ViewWorkPackage(CPOPortalBaseModel):
    __tablename__ = "_work-package"
    __table_args__ = {'schema': config.CPO_PORTAL_SCHEMA}

    work_package_name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    example_description = sa.Column(sa.Text)
    is_custom = sa.Column(sa.Boolean, default=False)
    complexity_level = sa.Column(sa.Integer, nullable=False)
    estimate = sa.Column(sa.Interval)
    type_list = sa.Column(pg.ARRAY(sa.String))
    credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    architectural_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    development_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    operation_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    upfront_cost = sa.Column(sa.Numeric(10, 2), nullable=False)
    monthly_cost = sa.Column(sa.Numeric(10, 2), nullable=False)
    work_item_count = sa.Column(sa.Integer, nullable=False)


# ================ Workflow Context ================
# Workflow Aggregate Root


class Workflow(CPOPortalBaseModel):
    __tablename__ = "workflow"

    entity_type = sa.Column(
        sa.Enum(types.EntityType, name="entity_type",
                schema=config.CPO_PORTAL_SCHEMA),
        nullable=False
    )
    name = sa.Column(sa.String(255), nullable=False)


# Workflow Status Entity
class WorkflowStatus(CPOPortalBaseModel):
    __tablename__ = "workflow-status"

    workflow_id = sa.Column(sa.ForeignKey(Workflow._id), nullable=False)
    key = sa.Column(sa.String(100), nullable=False, unique=True)
    is_start = sa.Column(sa.Boolean, default=False)
    is_end = sa.Column(sa.Boolean, default=False)


# Workflow Transition Entity
class WorkflowTransition(CPOPortalBaseModel):
    __tablename__ = "workflow-transition"

    workflow_id = sa.Column(sa.ForeignKey(Workflow._id), nullable=False)
    src_status_id = sa.Column(sa.ForeignKey(
        WorkflowStatus._id), nullable=False)
    dst_status_id = sa.Column(sa.ForeignKey(
        WorkflowStatus._id), nullable=False)
    rule_code = sa.Column(sa.String(100))
    condition = sa.Column(sa.Text)

# ================ Integration Context ================
# Integration Aggregate Root


class Integration(CPOPortalBaseModel):
    __tablename__ = "integration"

    # 'ticket' or 'project'
    entity_type = sa.Column(sa.String(100), nullable=False)
    # FK to project(_id) or ticket(_id)
    entity_id = sa.Column(pg.UUID, nullable=False)
    provider = sa.Column(sa.String(100), nullable=False)  # FK to ref--provider
    external_id = sa.Column(sa.String(255), nullable=False)
    external_url = sa.Column(sa.String(500))
    status = sa.Column(
        sa.Enum(types.SyncStatus, name="sync_status",
                schema=config.CPO_PORTAL_SCHEMA),
        nullable=False
    )


# ================ Notification Context ================
# Notification Aggregate Root
class Notification(CPOPortalBaseModel):
    __tablename__ = "notification"

    user_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)
    source_entity_type = sa.Column(sa.String(100), nullable=False)
    source_entity_id = sa.Column(pg.UUID, nullable=False)
    message = sa.Column(sa.Text, nullable=False)
    # FK to ref--notification-type
    type = sa.Column(sa.String(100), nullable=False)
    is_read = sa.Column(sa.Boolean, default=False)


class RefNotificationType(CPOPortalBaseModel):
    __tablename__ = "ref--notification-type"

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)
