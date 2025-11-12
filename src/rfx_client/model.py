import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg

from . import types, config


class RFXClientConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_client.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class RFXClientBaseModel(RFXClientConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

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
    category = sa.Column(sa.String(100))  # FK to ref__project_category
    priority = sa.Column(
        sa.Enum(
            types.PriorityEnum, name="priorityenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        nullable=False,
    )
    status = sa.Column(sa.String(100), nullable=False)
    start_date = sa.Column(sa.DateTime(timezone=True))
    target_date = sa.Column(sa.DateTime(timezone=True))
    duration = sa.Column(sa.Interval)
    free_credit_applied = sa.Column(sa.Integer, default=0)
    referral_code_used = sa.Column(sa.String(50))
    sync_status = sa.Column(
        sa.Enum(
            types.SyncStatusEnum, name="syncstatusenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        default=types.SyncStatusEnum.PENDING,
    )
    organization_id = sa.Column(pg.UUID)
    duration_text = sa.Column(sa.String(255))


class ViewProject(RFXClientBaseModel):
    __tablename__ = "_project"
    __ts_index__ = ["name", "description"]

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    category = sa.Column(sa.String(100))  # FK to ref__project_category
    priority = sa.Column(
        sa.Enum(
            types.PriorityEnum, name="priorityenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        nullable=False,
    )
    status = sa.Column(sa.String(100), nullable=False)
    start_date = sa.Column(sa.DateTime(timezone=True))
    target_date = sa.Column(sa.DateTime(timezone=True))
    duration = sa.Column(sa.Interval)
    free_credit_applied = sa.Column(sa.Integer, default=0)
    referral_code_used = sa.Column(sa.String(50))
    sync_status = sa.Column(
        sa.Enum(
            types.SyncStatusEnum, name="syncstatusenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        default=types.SyncStatusEnum.PENDING,
    )
    members = sa.Column(pg.ARRAY(pg.UUID))
    organization_id = sa.Column(pg.UUID)
    duration_text = sa.Column(sa.String(255))
    total_credit = sa.Column(sa.Float(), nullable=False)
    used_credit = sa.Column(sa.Float(), nullable=False)


# Project Milestone Entity
class ProjectMilestone(RFXClientBaseModel):
    __tablename__ = "project_milestone"
    __ts_index__ = ["name", "description"]

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    due_date = sa.Column(sa.DateTime(timezone=True), nullable=False)
    completed_at = sa.Column(sa.DateTime(timezone=True))
    is_completed = sa.Column(sa.Boolean, default=False)


# Project Ticket Entity
class ProjectTicket(RFXClientBaseModel):
    __tablename__ = "project_ticket"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    ticket_id = sa.Column(pg.UUID, nullable=False)  # FK to ticket(_id)


# Project Status Entity
class ProjectStatus(RFXClientBaseModel):
    __tablename__ = "project_status"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    # FK to workflow-status
    src_state = sa.Column(sa.String(100), nullable=False)
    # FK to workflow-status
    dst_state = sa.Column(sa.String(100), nullable=False)
    note = sa.Column(sa.Text)


# Project Member Entity
class ProjectMember(RFXClientBaseModel):
    __tablename__ = "project_member"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    member_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)
    role = sa.Column(sa.String(100), nullable=False)  # FK to ref__project_role
    permission = sa.Column(sa.String(255))


# Project Work Package Entity
class ProjectWorkPackage(RFXClientBaseModel):
    __tablename__ = "project_work_package"

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
    __tablename__ = "project_work_item"
    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2))
    credit_per_unit = sa.Column(sa.Numeric(10, 2))
    estimate = sa.Column(sa.Interval)
    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)


class ProjectWorkPackageWorkItem(RFXClientBaseModel):
    __tablename__ = "project_work_package_work_item"
    project_work_package_id = sa.Column(
        sa.ForeignKey(ProjectWorkPackage._id), nullable=False
    )
    project_work_item_id = sa.Column(sa.ForeignKey(ProjectWorkItem._id), nullable=False)
    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)


class ProjectWorkItemDeliverable(RFXClientBaseModel):
    __tablename__ = "project_work_item_deliverable"
    project_work_item_id = sa.Column(sa.ForeignKey(ProjectWorkItem._id), nullable=False)
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.Text)
    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)


class ViewProjectWorkPackage(RFXClientBaseModel):
    __tablename__ = "_project_work_package"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}
    __ts_index__ = [
        "work_package_name",
        "work_package_description",
        "work_package_example_description",
    ]

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
    __tablename__ = "_project_work_item"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}
    __ts_index__ = ["name", "description"]

    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)
    type_alias = sa.Column(sa.String(50), nullable=False)


class ViewProjectWorkItemListing(RFXClientBaseModel):
    __tablename__ = "_project_work_item_listing"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}
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


# Reference Tables
class RefProjectCategory(RFXClientBaseModel):
    __tablename__ = "ref__project_category"
    __ts_index__ = ["name", "description"]

    key = sa.Column(sa.String(50), nullable=False, unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)


class RefProjectRole(RFXClientBaseModel):
    __tablename__ = "ref__project_role"
    __ts_index__ = ["name", "description"]

    key = sa.Column(sa.String(50), nullable=False, unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_default = sa.Column(sa.Boolean, default=False)


# ================ Work Item Context ================
class WorkItem(RFXClientBaseModel):
    __tablename__ = "work_item"

    type = sa.Column(sa.String(50), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    price_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimate = sa.Column(sa.Interval)
    organization_id = sa.Column(pg.UUID)


class RefWorkItemType(RFXClientBaseModel):
    __tablename__ = "ref__work_item_type"
    __ts_index__ = ["name", "description"]

    key = sa.Column(sa.String(50), nullable=False, unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    alias = sa.Column(sa.String(50))


class WorkItemDeliverable(RFXClientBaseModel):
    __tablename__ = "work_item_deliverable"

    work_item_id = sa.Column(sa.ForeignKey(WorkItem._id), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)


class ViewWorkItem(RFXClientBaseModel):
    __tablename__ = "_work_item"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}
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
    __tablename__ = "_work_item_listing"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}
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
    __tablename__ = "work_package"

    work_package_name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    example_description = sa.Column(sa.Text)
    complexity_level = sa.Column(sa.Integer, default=1)
    estimate = sa.Column(sa.Interval)
    organization_id = sa.Column(pg.UUID)


class WorkPackageWorkItem(RFXClientBaseModel):
    __tablename__ = "work_package_work_item"

    work_package_id = sa.Column(sa.ForeignKey(WorkPackage._id), nullable=False)
    work_item_id = sa.Column(sa.ForeignKey(WorkItem._id), nullable=False)


class ViewWorkPackage(RFXClientBaseModel):
    __tablename__ = "_work_package"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}
    __ts_index__ = [
        "work_package_name",
        "description",
        "example_description",
        "type_list",
    ]

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
#     __tablename__ = "_custom_work_package"
#     __table_args__ = {'schema': config.RFX_CLIENT_SCHEMA}
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
        sa.Enum(
            types.SyncStatusEnum, name="syncstatusenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        nullable=False,
    )


# ================ Credit Usage ================


class ViewCreditUsage(RFXClientBaseModel):
    __tablename__ = "_credit_usage_summary"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    usage_year = sa.Column(sa.Integer, nullable=False)
    usage_month = sa.Column(sa.Integer, nullable=False)
    usage_week = sa.Column(sa.Integer, nullable=False)
    week_start_date = sa.Column(sa.DateTime(timezone=True), nullable=False)
    ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    de_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    op_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)


class ProjectIntegration(RFXClientBaseModel):
    __tablename__ = "project_integration"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}
    __ts_index__ = ["provider", "external_id", "external_url"]

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    provider = sa.Column(sa.String(100), nullable=False)
    external_id = sa.Column(sa.String(255), nullable=False)
    external_url = sa.Column(sa.String(500))


class ProjectMilestoneIntegration(RFXClientBaseModel):
    __tablename__ = "project_milestone_integration"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}
    __ts_index__ = ["provider", "external_id"]

    milestone_id = sa.Column(sa.ForeignKey(ProjectMilestone._id), nullable=False)
    provider = sa.Column(sa.String(100), nullable=False)
    external_id = sa.Column(sa.String(255), nullable=False)
    external_url = sa.Column(sa.String(500))


# =============== Model Ticket===============
class Ticket(RFXClientBaseModel):
    __tablename__ = "ticket"

    title = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    priority = sa.Column(
        sa.Enum(
            types.PriorityEnum, name="priorityenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        nullable=False,
    )
    type = sa.Column(sa.String(100), nullable=False)  # FK to ref--ticket-type
    parent_id = sa.Column(pg.UUID)  # FK to ticket(_id)
    assignee = sa.Column(pg.UUID)  # FK to profile(_id)
    status = sa.Column(sa.String(100), nullable=False)  # FK to ticket_status
    availability = sa.Column(
        sa.Enum(
            types.AvailabilityEnum,
            name="availabilityenum",
            schema=config.RFX_CLIENT_SCHEMA,
        ),
        nullable=False,
    )
    sync_status = sa.Column(
        sa.Enum(
            types.SyncStatusEnum, name="syncstatusenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        default=types.SyncStatusEnum.PENDING,
    )
    is_inquiry = sa.Column(sa.Boolean, default=True)
    organization_id = sa.Column(pg.UUID)


# Ticket Status Entity
class TicketStatus(RFXClientBaseModel):
    __tablename__ = "ticket_status"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    # FK to workflow-status
    src_state = sa.Column(sa.String(100), nullable=False)
    # FK to workflow-status
    dst_state = sa.Column(sa.String(100), nullable=False)
    note = sa.Column(sa.Text)


class TicketAssignee(RFXClientBaseModel):
    __tablename__ = "ticket_assignee"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    member_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)


# Ticket Participants Entity
class TicketParticipants(RFXClientBaseModel):
    __tablename__ = "ticket_participant"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    participant_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)


# Ticket Tag Entity
class TicketTag(RFXClientBaseModel):
    __tablename__ = "ticket_tag"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    tag_id = sa.Column(pg.UUID, nullable=False)  # FK to tag(_id)


class RefTicketType(RFXClientBaseModel):
    __tablename__ = "ref__ticket_type"

    key = sa.Column(sa.String(50), nullable=False, unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    icon_color = sa.Column(sa.String(7))  # Hex color code
    is_active = sa.Column(sa.Boolean, default=True)
    is_inquiry = sa.Column(sa.Boolean, default=True)


class TicketIntegration(RFXClientBaseModel):
    __tablename__ = "ticket_integration"
    __ts_index__ = ["provider", "external_id", "external_url"]

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    provider = sa.Column(sa.String(100), nullable=False)  # e.g., 'linear'
    external_id = sa.Column(sa.String(255), nullable=False)
    external_url = sa.Column(sa.String(255), nullable=False)


# ================ Tag Context ================s


# Tag Aggregate Root
class Tag(RFXClientBaseModel):
    __tablename__ = "tag"

    key = sa.Column(sa.String(50), nullable=False, unique=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)
    target_resource = sa.Column(sa.String(100), nullable=False)
    organization_id = sa.Column(pg.UUID)


# ================ Workflow Context ================


class Status(RFXClientBaseModel):
    __tablename__ = "status"

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    entity_type = sa.Column(sa.String(100), nullable=False)
    is_active = sa.Column(sa.Boolean, default=True)


class StatusKey(RFXClientBaseModel):
    __tablename__ = "status_key"

    status_id = sa.Column(sa.ForeignKey(Status._id), nullable=False)
    key = sa.Column(sa.String(100), nullable=False, unique=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_initial = sa.Column(sa.Boolean, default=False)
    is_final = sa.Column(sa.Boolean, default=False)


class StatusTransition(RFXClientBaseModel):
    __tablename__ = "status_transition"

    status_id = sa.Column(sa.ForeignKey(Status._id), nullable=False)
    src_status_key_id = sa.Column(sa.ForeignKey(StatusKey._id), nullable=False)
    dst_status_key_id = sa.Column(sa.ForeignKey(StatusKey._id), nullable=False)


class ViewStatus(RFXClientBaseModel):
    __tablename__ = "_status"

    entity_type = sa.Column(sa.String(100), nullable=False)
    status_id = sa.Column(pg.UUID, primary_key=True)
    key = sa.Column(sa.String(100), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_initial = sa.Column(sa.Boolean, nullable=False)
    is_final = sa.Column(sa.Boolean, nullable=False)


# View


class ViewInquiry(RFXClientBaseModel):
    __tablename__ = "_inquiry"

    type = sa.Column(sa.String(255), primary_key=True)
    type_icon_color = sa.Column(sa.String(7))  # Hex color code
    title = sa.Column(sa.String(255), nullable=False)
    tag_names = sa.Column(pg.ARRAY(sa.String))
    participants = sa.Column(pg.JSONB)
    activity = sa.Column(sa.DateTime)
    availability = sa.Column(
        sa.Enum(
            types.AvailabilityEnum,
            name="availabilityenum",
            schema=config.RFX_CLIENT_SCHEMA,
        ),
        nullable=False,
    )
    organization_id = sa.Column(pg.UUID)


class ViewTicket(RFXClientBaseModel):
    __tablename__ = "_ticket"

    title = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    priority = sa.Column(sa.String(100), nullable=False)
    type = sa.Column(sa.String(100), nullable=False)
    parent_id = sa.Column(pg.UUID)
    assignee = sa.Column(pg.UUID)
    status = sa.Column(sa.String(100), nullable=False)
    availability = sa.Column(
        sa.Enum(
            types.AvailabilityEnum,
            name="availabilityenum",
            schema=config.RFX_CLIENT_SCHEMA,
        ),
        nullable=False,
    )
    sync_status = sa.Column(
        sa.Enum(
            types.SyncStatusEnum, name="syncstatusenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        default=types.SyncStatusEnum.PENDING,
    )
    project_id = sa.Column(pg.UUID)
    organization_id = sa.Column(pg.UUID)


# ---------- comment context-------------
class Comment(RFXClientBaseModel):
    __tablename__ = "comment"

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    organization_id = sa.Column(pg.UUID)
    resource = sa.Column(sa.String(100))
    resource_id = sa.Column(pg.UUID)
    source = sa.Column(sa.String(100))  # e.g., 'user', 'system', 'linear'


class CommentIntegration(RFXClientBaseModel):
    __tablename__ = "comment_integration"
    __ts_index__ = ["provider", "external_id", "external_url"]

    comment_id = sa.Column(sa.ForeignKey(Comment._id), nullable=False)
    provider = sa.Column(sa.String(100), nullable=False)  # e.g., 'linear'
    external_id = sa.Column(sa.String(255), nullable=False)
    external_url = sa.Column(sa.String(255), nullable=False)
    source = sa.Column(sa.String(100))  # e.g., 'user', 'system', 'linear'


class CommentView(RFXClientBaseModel):
    __tablename__ = "_comment"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    creator = sa.Column(pg.JSONB)
    organization_id = sa.Column(pg.UUID)
    resource = sa.Column(sa.String(100))
    resource_id = sa.Column(pg.UUID)
    source = sa.Column(sa.String(100))  # e.g., 'user', 'system', 'linear'


class CommentAttachment(RFXClientBaseModel):
    __tablename__ = "comment_attachment"

    comment_id = sa.Column(pg.UUID, nullable=False)

    media_entry_id = sa.Column(pg.UUID, nullable=False)

    attachment_type = sa.Column(sa.String(50))
    caption = sa.Column(sa.Text)
    display_order = sa.Column(sa.Integer, default=0)
    is_primary = sa.Column(sa.Boolean, default=False)


class CommentAttachmentView(RFXClientBaseModel):
    __tablename__ = "_comment_attachment"

    comment_id = sa.Column(pg.UUID)
    media_entry_id = sa.Column(pg.UUID)

    attachment_type = sa.Column(sa.String(50))
    caption = sa.Column(sa.Text)
    display_order = sa.Column(sa.Integer)
    is_primary = sa.Column(sa.Boolean)

    filename = sa.Column(sa.String(1024))
    filehash = sa.Column(sa.String(64))
    filemime = sa.Column(sa.String(256))
    length = sa.Column(sa.BigInteger)
    fspath = sa.Column(sa.String(1024))
    fskey = sa.Column(sa.String(24))
    compress = sa.Column(sa.String(50))
    cdn_url = sa.Column(sa.String(1024))

    resource = sa.Column(sa.String(24))
    resource__id = sa.Column(pg.UUID)

    uploader = sa.Column(pg.JSONB)


class CommentReaction(RFXClientBaseModel):
    __tablename__ = "comment_reaction"

    comment_id = sa.Column(pg.UUID, nullable=False)
    user_id = sa.Column(pg.UUID, nullable=False)
    reaction_type = sa.Column(sa.String(50), nullable=False)


class CommentReactionView(RFXClientBaseModel):
    __tablename__ = "_comment_reaction"

    comment_id = sa.Column(pg.UUID)
    user_id = sa.Column(pg.UUID)
    reaction_type = sa.Column(sa.String(50))
    reactor = sa.Column(pg.JSONB)


class CommentReactionSummary(RFXClientBaseModel):
    """Aggregated reaction counts per comment and type"""

    __tablename__ = "_comment_reaction_summary"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    comment_id = sa.Column(pg.UUID)
    reaction_type = sa.Column(sa.String(50))
    reaction_count = sa.Column(sa.Integer)
    users = sa.Column(pg.JSONB)


# === Credit Transaction Context ===#\


class CreditBalance(RFXClientBaseModel):
    """
    Credit Balance - Số dư credit của organization

    Mỗi organization có 1 credit pool với 3 loại credit:
    - ar_credits: Architectural Credits
    - de_credits: Development Credits
    - op_credits: Operation Credits
    """

    __tablename__ = "credit_balance"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    organization_id = sa.Column(pg.UUID, nullable=False, unique=True)
    ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    de_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    op_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    total_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)

    total_purchased_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    total_used = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    total_refunded_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)

    last_purchase_date = sa.Column(sa.DateTime(timezone=True))
    last_usage_date = sa.Column(sa.DateTime(timezone=True))
    last_refund_date = sa.Column(sa.DateTime(timezone=True))
    avg_daily_usage = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    avg_weekly_usage = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)

    estimated_depletion_date = sa.Column(sa.DateTime(timezone=True))
    day_until_depletion = sa.Column(sa.Integer, nullable=False, default=0)
    is_low_blance = sa.Column(sa.Boolean, default=False)
    low_balance_threshold = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)


class CreditPurchase(RFXClientBaseModel):
    """
    Credit Purchase Transaction

    Ghi nhận lịch sử mua credit:
    - Số lượng credit mua
    - Phân bổ theo loại (AR/DE/OP)
    - Thông tin thanh toán
    - Trạng thái giao dịch
    """

    __tablename__ = "credit_purchase"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    organization_id = sa.Column(pg.UUID, nullable=False)
    purchase_amount = sa.Column(sa.Numeric(10, 2), nullable=False)
    ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    de_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    op_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)

    amount = sa.Column(sa.Numeric(10, 2), nullable=False)
    currency = sa.Column(sa.String(10), nullable=False)
    payment_method = sa.Column(sa.String(50))
    transaction_id = sa.Column(sa.String(100))
    invoice_number = sa.Column(sa.String(100))
    status = sa.Column(sa.String(50), nullable=False)

    discount_code = sa.Column(sa.String(50))
    discount_amount = sa.Column(sa.Numeric(10, 2), default=0)
    note = sa.Column(sa.Text)
    payment_info = sa.Column(pg.JSONB)
    transaction_status = sa.Column(sa.String(50))

    purchased_by = sa.Column(pg.UUID, nullable=False)  # profile(_id)
    completed_date = sa.Column(sa.DateTime(timezone=True))
    package_id = sa.Column(pg.UUID)  # credit_package(_id)
    refund_date = sa.Column(sa.DateTime(timezone=True))
    refund_reason = sa.Column(sa.Text)
    refund_amount = sa.Column(sa.Numeric(10, 2))


class CreditUsageLog(RFXClientBaseModel):
    """
    Credit Usage Log

    Ghi nhận mỗi lần sử dụng credit:
    - Từ Work Package nào
    - Work Item nào
    - Số credit tiêu thụ
    - Loại credit (AR/DE/OP)
    """

    __tablename__ = "credit_usage_log"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    organization_id = sa.Column(pg.UUID, nullable=False)
    project_id = sa.Column(pg.UUID, nullable=False)
    work_package_id = sa.Column(pg.UUID, nullable=False)
    work_item_id = sa.Column(pg.UUID, nullable=False)
    work_type = sa.Column(sa.String(50), nullable=False)

    credit_used = sa.Column(sa.Numeric(10, 2), nullable=False)
    credit_per_unit = sa.Column(sa.Numeric(10, 2), nullable=False)
    units_consumed = sa.Column(sa.Integer, nullable=False, default=1)
    used_by = sa.Column(pg.UUID, nullable=False)  # profile(_id)
    description = sa.Column(sa.Text)

    is_refunded = sa.Column(sa.Boolean, default=False)
    refund_date = sa.Column(sa.DateTime(timezone=True))
    refund_reason = sa.Column(sa.Text)
    refund_amount = sa.Column(sa.Numeric(10, 2))


class CreditPackage(RFXClientBaseModel):
    """
    Credit Package - Gói credit định sẵn

    Các gói credit có thể mua:
    - Starter Pack: 100 credits
    - Professional: 500 credits
    - Enterprise: 2000 credits
    - Custom
    """

    __tablename__ = "credit_package"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    package_name = sa.Column(sa.String(100), nullable=False, unique=True)
    package_code = sa.Column(sa.String(50), nullable=False, unique=True)
    ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    de_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    op_credits = sa.Column(sa.Numeric(10, 2), nullable=False, default=0)
    total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    price = sa.Column(sa.Numeric(10, 2), nullable=False)
    currency = sa.Column(sa.String(10), nullable=False)
    description = sa.Column(sa.Text)
    featured = sa.Column(sa.Boolean, default=False)
    is_active = sa.Column(sa.Boolean, default=True)


# ------- views for credit-----------
class CreditSummaryView(RFXClientBaseModel):
    __tablename__ = "_credit_summary"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    organization_id = sa.Column(pg.UUID, primary_key=True)
    current_ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    current_de_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    current_op_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    current_total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)

    total_purchased_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    remaining_percentage = sa.Column(sa.Numeric(5, 2), nullable=False)

    avg_daily_usage = sa.Column(sa.Numeric(10, 2), nullable=False)
    avg_weekly_usage = sa.Column(sa.Numeric(10, 2), nullable=False)

    month_purchased = sa.Column(sa.Numeric(10, 2), nullable=False)
    month_used = sa.Column(sa.Numeric(10, 2), nullable=False)

    last_purchase_date = sa.Column(sa.DateTime(timezone=True))
    last_usage_date = sa.Column(sa.DateTime(timezone=True))


class CreditUsageWeeklyView(RFXClientBaseModel):
    __tablename__ = "_credit_usage_weekly"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    organization_id = sa.Column(pg.UUID, primary_key=True)
    usage_year = sa.Column(sa.Integer, primary_key=True)
    usage_week = sa.Column(sa.Integer, primary_key=True)

    week_start_date = sa.Column(sa.DateTime(timezone=True), nullable=False)
    week_end_date = sa.Column(sa.DateTime(timezone=True), nullable=False)

    total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    de_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    op_credits = sa.Column(sa.Numeric(10, 2), nullable=False)

    usage_count = sa.Column(sa.Integer, nullable=False)
    project_count = sa.Column(sa.Integer, nullable=False)
    work_package_count = sa.Column(sa.Integer, nullable=False)

    week_over_week_change = sa.Column(sa.Numeric(5, 2), nullable=False)
    week_over_week_percentage = sa.Column(sa.Numeric(5, 2), nullable=False)


class CreditUsageDailyView(RFXClientBaseModel):
    __tablename__ = "_credit_usage_daily"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    organization_id = sa.Column(pg.UUID, primary_key=True)
    usage_date = sa.Column(sa.Date, primary_key=True)

    total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    de_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    op_credits = sa.Column(sa.Numeric(10, 2), nullable=False)

    usage_count = sa.Column(sa.Integer, nullable=False)


class ProjectCreditUsageView(RFXClientBaseModel):
    __tablename__ = "_project_credit_usage"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    project_id = sa.Column(pg.UUID, primary_key=True)
    organization_id = sa.Column(pg.UUID, nullable=False)
    project_name = sa.Column(sa.String(255), nullable=False)

    ar_credits_used = sa.Column(sa.Numeric(10, 2), nullable=False)
    de_credits_used = sa.Column(sa.Numeric(10, 2), nullable=False)
    op_credits_used = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_credits_used = sa.Column(sa.Numeric(10, 2), nullable=False)

    estimated_total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    variance = sa.Column(sa.Numeric(10, 2), nullable=False)
    variance_percentage = sa.Column(sa.Numeric(5, 2), nullable=False)

    total_work_packages = sa.Column(sa.Integer, nullable=False)
    completed_work_packages = sa.Column(sa.Integer, nullable=False)
    in_progess_work_packages = sa.Column(sa.Integer, nullable=False)

    first_usage_date = sa.Column(sa.DateTime(timezone=True))
    last_usage_date = sa.Column(sa.DateTime(timezone=True))

    project_status = sa.Column(sa.String(100), nullable=False)


class WorkPackageCreditUsageView(RFXClientBaseModel):
    __tablename__ = "_work_package_credit_usage"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    work_package_id = sa.Column(pg.UUID, primary_key=True)
    project_id = sa.Column(pg.UUID, nullable=False)
    organization_id = sa.Column(pg.UUID, nullable=False)
    work_package_name = sa.Column(sa.String(255), nullable=False)

    estimated_ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimated_de_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimated_op_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    estimated_total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)

    actual_ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    actual_de_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    actual_op_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    actual_total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)

    variance_ar = sa.Column(sa.Numeric(10, 2), nullable=False)
    variance_de = sa.Column(sa.Numeric(10, 2), nullable=False)
    variance_op = sa.Column(sa.Numeric(10, 2), nullable=False)
    variance_total = sa.Column(sa.Numeric(10, 2), nullable=False)

    variance_percentage = sa.Column(sa.Numeric(5, 2), nullable=False)

    completion_precentage = sa.Column(sa.Numeric(5, 2), nullable=False)
    credits_remaining = sa.Column(sa.Numeric(10, 2), nullable=False)

    total_work_items = sa.Column(sa.Integer, nullable=False)
    completed_work_items = sa.Column(sa.Integer, nullable=False)

    status = sa.Column(sa.String(100), nullable=False)


class CreditPurchaseHistoryView(RFXClientBaseModel):
    __tablename__ = "_credit_purchase_history"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    purchase_id = sa.Column(pg.UUID, primary_key=True)
    organization_id = sa.Column(pg.UUID, nullable=False)
    purchase_date = sa.Column(sa.DateTime(timezone=True), nullable=False)

    ar_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    de_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    op_credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    total_credits = sa.Column(sa.Numeric(10, 2), nullable=False)

    amount = sa.Column(sa.Numeric(12, 2))
    currency = sa.Column(sa.String(10))
    payment_method = sa.Column(sa.String(50))
    transaction_id = sa.Column(sa.String(100))
    invoice_number = sa.Column(sa.String(100))

    # === Discount ===
    discount_code = sa.Column(sa.String(50))
    discount_amount = sa.Column(sa.Numeric(12, 2))
    final_amount = sa.Column(sa.Numeric(12, 2), comment="amount - discount")

    # === Status ===
    status = sa.Column(sa.String(50))

    # === Package Info ===
    package_name = sa.Column(sa.String(100), comment="If from a package")
    package_code = sa.Column(sa.String(50))

    # === User Info ===
    purchased_by = sa.Column(pg.UUID)
    purchaser_name = sa.Column(sa.String(255))
    purchaser_email = sa.Column(sa.String(255))


class OrganizationCreditSummaryView(RFXClientBaseModel):
    """
    Organization Credit Summary View

    Tổng quan credit của organization:
    - Total credits (balance, allocated, used, available)
    - Credits by type (AR/DE/OP)
    - Usage statistics (allocation %, completion %)
    - Project counts
    - Low balance alerts
    """

    __tablename__ = "_organization_credit_summary"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    organization_id = sa.Column(pg.UUID, nullable=False)

    # Total credits
    total_credits = sa.Column(sa.Numeric(12, 2), nullable=False)
    total_purchased_credits = sa.Column(sa.Numeric(12, 2), nullable=False)
    total_allocated = sa.Column(sa.Numeric(12, 2), nullable=False)
    total_used = sa.Column(sa.Numeric(12, 2), nullable=False)
    total_available = sa.Column(sa.Numeric(12, 2), nullable=False)

    # Architecture credits
    ar_credits_balance = sa.Column(sa.Numeric(12, 2), nullable=False)
    ar_credits_allocated = sa.Column(sa.Numeric(12, 2), nullable=False)
    ar_credits_used = sa.Column(sa.Numeric(12, 2), nullable=False)
    ar_credits_available = sa.Column(sa.Numeric(12, 2), nullable=False)

    # Development credits
    de_credits_balance = sa.Column(sa.Numeric(12, 2), nullable=False)
    de_credits_allocated = sa.Column(sa.Numeric(12, 2), nullable=False)
    de_credits_used = sa.Column(sa.Numeric(12, 2), nullable=False)
    de_credits_available = sa.Column(sa.Numeric(12, 2), nullable=False)

    # Operation credits
    op_credits_balance = sa.Column(sa.Numeric(12, 2), nullable=False)
    op_credits_allocated = sa.Column(sa.Numeric(12, 2), nullable=False)
    op_credits_used = sa.Column(sa.Numeric(12, 2), nullable=False)
    op_credits_available = sa.Column(sa.Numeric(12, 2), nullable=False)

    # Statistics
    allocation_percentage = sa.Column(sa.Numeric(5, 2), nullable=False)
    completion_percentage = sa.Column(sa.Numeric(5, 2), nullable=False)

    # Project stats
    total_projects = sa.Column(sa.Integer, nullable=False)
    active_projects = sa.Column(sa.Integer, nullable=False)

    # Alerts
    is_low_balance = sa.Column(sa.Boolean, nullable=False)
    low_balance_threshold = sa.Column(sa.Numeric(12, 2), nullable=False)


# ================ Project Credit Summary View ================


class ProjectCreditSummaryView(RFXClientBaseModel):
    """
    Project Credit Summary View

    Chi tiết credit của từng project:
    - Total credits (estimated)
    - Credit used (DONE work packages)
    - Actual credits (from usage log)
    - Credits remaining
    - Completion percentage
    - Work package/item counts
    """

    __tablename__ = "_project_credit_summary"
    __table_args__ = {"schema": config.RFX_CLIENT_SCHEMA}

    project_id = sa.Column(pg.UUID, nullable=False)
    organization_id = sa.Column(pg.UUID, nullable=False)
    project_name = sa.Column(sa.String(255), nullable=False)
    project_status = sa.Column(sa.String(100), nullable=False)

    # Credits
    total_credits = sa.Column(
        sa.Numeric(12, 2),
        nullable=False,
        comment="Estimated total credits for all work items",
    )
    credit_used = sa.Column(
        sa.Numeric(12, 2), nullable=False, comment="Credits from DONE work packages"
    )
    actual_total_credits = sa.Column(
        sa.Numeric(12, 2), nullable=False, comment="Actual credits from usage log"
    )
    credits_remaining = sa.Column(
        sa.Numeric(12, 2), nullable=False, comment="total_credits - credit_used"
    )

    # Progress
    completion_percentage = sa.Column(
        sa.Numeric(5, 2), nullable=False, comment="(credit_used / total_credits) * 100"
    )

    # Work Package Stats
    total_work_packages = sa.Column(sa.Integer, nullable=False)
    completed_work_packages = sa.Column(
        sa.Integer, nullable=False, comment="Work packages with status = DONE"
    )

    # Work Item Count
    total_work_items = sa.Column(sa.Integer, nullable=False)


class ViewProjectDetail(RFXClientBaseModel):
    __tablename__ = "_project_detail"
    __ts_index__ = ["name", "description"]

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    category = sa.Column(sa.String(100))  # FK to ref__project_category
    priority = sa.Column(
        sa.Enum(
            types.PriorityEnum, name="priorityenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        nullable=False,
    )
    status = sa.Column(sa.String(100), nullable=False)
    start_date = sa.Column(sa.DateTime(timezone=True))
    target_date = sa.Column(sa.DateTime(timezone=True))
    duration = sa.Column(sa.Interval)
    free_credit_applied = sa.Column(sa.Integer, default=0)
    referral_code_used = sa.Column(sa.String(50))
    sync_status = sa.Column(
        sa.Enum(
            types.SyncStatusEnum, name="syncstatusenum", schema=config.RFX_CLIENT_SCHEMA
        ),
        default=types.SyncStatusEnum.PENDING,
    )
    members = sa.Column(pg.ARRAY(pg.UUID))
    organization_id = sa.Column(pg.UUID)
    duration_text = sa.Column(sa.String(255))
    total_credit = sa.Column(sa.Float(), nullable=False)
    used_credit = sa.Column(sa.Float(), nullable=False)
