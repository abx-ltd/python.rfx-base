import array
import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg


from . import types, config


class RFXClientConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_client.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class RFXClientBaseModel(RFXClientConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}

    _realm = sa.Column(sa.String)

# ================ Promotion Context ================


class Promotion(RFXClientBaseModel):
    __tablename__ = "promotion"

    code = sa.Column(sa.String(50), nullable=False, unique=True)
    valid_from = sa.Column(sa.DateTime(timezone=True), nullable=False)
    valid_until = sa.Column(sa.DateTime(timezone=True), nullable=False)
    max_uses = sa.Column(sa.Integer, nullable=False)
    current_uses = sa.Column(sa.Integer, default=0)
    discount_value = sa.Column(sa.Numeric(10, 2), nullable=False)
    organization_id = sa.Column(pg.UUID)


# ================ Project Context ================
# Project Aggregate Root
class Project(RFXClientBaseModel):
    __tablename__ = "project"

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    category = sa.Column(sa.String(100))  # FK to ref--project-category
    priority = sa.Column(
        sa.Enum(types.Priority, name="priority",
                schema=config.CPO_CLIENT_SCHEMA),
        nullable=False
    )
    status = sa.Column(sa.String(100), nullable=False)
    start_date = sa.Column(sa.DateTime(timezone=True))
    target_date = sa.Column(sa.DateTime(timezone=True))
    duration = sa.Column(sa.Interval)
    free_credit_applied = sa.Column(sa.Integer, default=0)
    referral_code_used = sa.Column(sa.String(50))
    sync_status = sa.Column(
        sa.Enum(types.SyncStatus, name="sync_status",
                schema=config.CPO_CLIENT_SCHEMA),
        default=types.SyncStatus.PENDING
    )
    organization_id = sa.Column(pg.UUID)
    duration_text = sa.Column(sa.String(255))


class ViewProject(RFXClientBaseModel):
    __tablename__ = "_project"
    __ts_index__ = ["name", "description"]

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    category = sa.Column(sa.String(100))  # FK to ref--project-category
    priority = sa.Column(
        sa.Enum(types.Priority, name="priority",
                schema=config.CPO_CLIENT_SCHEMA),
        nullable=False
    )
    status = sa.Column(sa.String(100), nullable=False)
    start_date = sa.Column(sa.DateTime(timezone=True))
    target_date = sa.Column(sa.DateTime(timezone=True))
    duration = sa.Column(sa.Interval)
    free_credit_applied = sa.Column(sa.Integer, default=0)
    referral_code_used = sa.Column(sa.String(50))
    sync_status = sa.Column(
        sa.Enum(types.SyncStatus, name="sync_status",
                schema=config.CPO_CLIENT_SCHEMA),
        default=types.SyncStatus.PENDING
    )
    members = sa.Column(pg.ARRAY(pg.UUID))
    organization_id = sa.Column(pg.UUID)
    duration_text = sa.Column(sa.String(255))


# Project Milestone Entity
class ProjectMilestone(RFXClientBaseModel):
    __tablename__ = "project-milestone"
    __ts_index__ = ["name", "description"]

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    due_date = sa.Column(sa.DateTime(timezone=True), nullable=False)
    completed_at = sa.Column(sa.DateTime(timezone=True))
    is_completed = sa.Column(sa.Boolean, default=False)


# Project Ticket Entity
class ProjectTicket(RFXClientBaseModel):
    __tablename__ = "project-ticket"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    ticket_id = sa.Column(pg.UUID, nullable=False)  # FK to ticket(_id)


# Project Status Entity
class ProjectStatus(RFXClientBaseModel):
    __tablename__ = "project-status"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    # FK to workflow-status
    src_state = sa.Column(sa.String(100), nullable=False)
    # FK to workflow-status
    dst_state = sa.Column(sa.String(100), nullable=False)
    note = sa.Column(sa.Text)


# Project Member Entity
class ProjectMember(RFXClientBaseModel):
    __tablename__ = "project-member"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    member_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)
    role = sa.Column(sa.String(100), nullable=False)  # FK to ref--project-role
    permission = sa.Column(sa.String(255))


# Project Work Package Entity
class ProjectWorkPackage(RFXClientBaseModel):
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


class ProjectWorkItem(RFXClientBaseModel):
    __tablename__ = "project-work-item"
    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2))
    credit_per_unit = sa.Column(sa.Numeric(10, 2))
    estimate = sa.Column(sa.Interval)
    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)


class ProjectWorkPackageWorkItem(RFXClientBaseModel):
    __tablename__ = "project-work-package-work-item"
    project_work_package_id = sa.Column(
        sa.ForeignKey(ProjectWorkPackage._id), nullable=False)
    project_work_item_id = sa.Column(sa.ForeignKey(
        ProjectWorkItem._id), nullable=False)
    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)


class ProjectWorkItemDeliverable(RFXClientBaseModel):
    __tablename__ = "project-work-item-deliverable"
    project_work_item_id = sa.Column(sa.ForeignKey(
        ProjectWorkItem._id), nullable=False)
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.Text)
    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)


class ViewProjectWorkPackage(RFXClientBaseModel):
    __tablename__ = "_project-work-package"
    __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}
    __ts_index__ = ["work_package_name", "work_package_description",
                    "work_package_example_description"]

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


class ViewProjectWorkItem(RFXClientBaseModel):
    __tablename__ = "_project-work-item"
    __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}
    __ts_index__ = ["name", "description"]

    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)
    type_alias = sa.Column(sa.String(50), nullable=False)


class ViewProjectWorkItemListing(RFXClientBaseModel):
    __tablename__ = "_project-work-item-listing"
    __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}
    __ts_index__ = ["project_work_item_name", "project_work_item_description"]

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


class ProjectBDMContact(RFXClientBaseModel):
    __tablename__ = "project-bdm-contact"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    contact_method = sa.Column(pg.ARRAY(sa.Enum(types.ContactMethod, name="contact_method",
                                                schema=config.CPO_CLIENT_SCHEMA)), nullable=False)
    message = sa.Column(sa.Text)
    meeting_time = sa.Column(sa.DateTime(timezone=True))
    status = sa.Column(sa.String(100), nullable=False)


class ViewProjectEstimateSummary(RFXClientBaseModel):
    __tablename__ = "_project-estimate-summary"
    __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}

    architectural_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    development_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    operation_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    discount_value = sa.Column(sa.Numeric(10, 2), nullable=False)
    free_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_credits_raw = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_credits_after_discount = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_cost = sa.Column(sa.Numeric(10, 2), nullable=False)


# Reference Tables
class RefProjectCategory(RFXClientBaseModel):
    __tablename__ = "ref--project-category"
    __ts_index__ = ["name", "description"]

    key = sa.Column(sa.String(50), nullable=False,
                    unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)


class RefProjectRole(RFXClientBaseModel):
    __tablename__ = "ref--project-role"
    __ts_index__ = ["name", "description"]

    key = sa.Column(sa.String(50), nullable=False,
                    unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_default = sa.Column(sa.Boolean, default=False)


# ================ Work Item Context ================
class WorkItem(RFXClientBaseModel):
    __tablename__ = "work-item"

    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)
    organization_id = sa.Column(pg.UUID)


class RefWorkItemType(RFXClientBaseModel):
    __tablename__ = "ref--work-item-type"
    __ts_index__ = ["name", "description"]

    key = sa.Column(sa.String(50), nullable=False,
                    unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    alias = sa.Column(sa.String(50))


class WorkItemDeliverable(RFXClientBaseModel):
    __tablename__ = "work-item-deliverable"

    work_item_id = sa.Column(sa.ForeignKey(WorkItem._id), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)


class ViewWorkItem(RFXClientBaseModel):
    __tablename__ = "_work-item"
    __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}
    __ts_index__ = ["name", "description"]

    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)
    type_alias = sa.Column(sa.String(50), nullable=False)
    organization_id = sa.Column(pg.UUID)


class ViewWorkItemListing(RFXClientBaseModel):
    __tablename__ = "_work-item-listing"
    __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}
    __ts_index__ = ["work_item_name", "work_item_description"]

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
    organization_id = sa.Column(pg.UUID)


# ================ Work Package Context ================
# Work Package Aggregate Root


class WorkPackage(RFXClientBaseModel):
    __tablename__ = "work-package"

    work_package_name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    example_description = sa.Column(sa.Text)
    complexity_level = sa.Column(sa.Integer, default=1)
    estimate = sa.Column(sa.Interval)
    organization_id = sa.Column(pg.UUID)


class WorkPackageWorkItem(RFXClientBaseModel):
    __tablename__ = "work-package-work-item"

    work_package_id = sa.Column(sa.ForeignKey(WorkPackage._id), nullable=False)
    work_item_id = sa.Column(sa.ForeignKey(WorkItem._id), nullable=False)


class ViewWorkPackage(RFXClientBaseModel):
    __tablename__ = "_work-package"
    __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}
    __ts_index__ = ["work_package_name", "description",
                    "example_description", "type_list"]

    work_package_name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    example_description = sa.Column(sa.Text)
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
    organization_id = sa.Column(pg.UUID)
    is_custom = sa.Column(sa.Boolean)


# class ViewCustomWorkPackage(RFXClientBaseModel):
#     __tablename__ = "_custom-work-package"
#     __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}
#     __ts_index__ = ["work_package_name", "description",
#                     "example_description", "type_list"]

#     work_package_name = sa.Column(sa.String(255), nullable=False)
#     description = sa.Column(sa.Text)
#     example_description = sa.Column(sa.Text)
#     complexity_level = sa.Column(sa.Integer, nullable=False)
#     estimate = sa.Column(sa.Interval)
#     type_list = sa.Column(pg.ARRAY(sa.String))
#     credits = sa.Column(sa.Numeric(10, 2), nullable=False)
#     architectural_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
#     development_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
#     operation_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
#     upfront_cost = sa.Column(sa.Numeric(10, 2), nullable=False)
#     monthly_cost = sa.Column(sa.Numeric(10, 2), nullable=False)
#     work_item_count = sa.Column(sa.Integer, nullable=False)
#     organization_id = sa.Column(pg.UUID)


# ================ Integration Context ================
# Integration Aggregate Root


class Integration(RFXClientBaseModel):
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
                schema=config.CPO_CLIENT_SCHEMA),
        nullable=False
    )


# ================ Credit Usage ================

class ViewCreditUsage(RFXClientBaseModel):
    __tablename__ = "_credit-usage-summary"
    __table_args__ = {'schema': config.CPO_CLIENT_SCHEMA}

    usage_year = sa.Column(sa.Integer, nullable=False)
    usage_month = sa.Column(sa.Integer, nullable=False)
    usage_week = sa.Column(sa.Integer, nullable=False)
    week_start_date = sa.Column(sa.DateTime(timezone=True), nullable=False)
    ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    de_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    op_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)


