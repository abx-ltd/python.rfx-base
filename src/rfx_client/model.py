import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver
from sqlalchemy.dialects import postgresql as pg


from . import types, config


class RFXClientConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_client.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class RFXClientBaseModel(RFXClientConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}

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
            types.PriorityEnum, name="priorityenum", schema=config.CPO_CLIENT_SCHEMA
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
            types.SyncStatusEnum, name="syncstatusenum", schema=config.CPO_CLIENT_SCHEMA
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
            types.PriorityEnum, name="priorityenum", schema=config.CPO_CLIENT_SCHEMA
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
            types.SyncStatusEnum, name="syncstatusenum", schema=config.CPO_CLIENT_SCHEMA
        ),
        default=types.SyncStatusEnum.PENDING,
    )
    members = sa.Column(pg.ARRAY(pg.UUID))
    organization_id = sa.Column(pg.UUID)
    duration_text = sa.Column(sa.String(255))


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
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}
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
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}
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
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}
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
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}
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
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}
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
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}
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
        sa.Enum(
            types.SyncStatusEnum, name="syncstatusenum", schema=config.CPO_CLIENT_SCHEMA
        ),
        nullable=False,
    )


# ================ Credit Usage ================


class ViewCreditUsage(RFXClientBaseModel):
    __tablename__ = "_credit_usage_summary"
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}

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
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}
    __ts_index__ = ["provider", "external_id", "external_url"]

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    provider = sa.Column(sa.String(100), nullable=False)
    external_id = sa.Column(sa.String(255), nullable=False)
    external_url = sa.Column(sa.String(500))


class ProjectMilestoneIntegration(RFXClientBaseModel):
    __tablename__ = "project_milestone_integration"
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}
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
            types.PriorityEnum, name="priorityenum", schema=config.CPO_CLIENT_SCHEMA
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
            schema=config.CPO_CLIENT_SCHEMA,
        ),
        nullable=False,
    )
    sync_status = sa.Column(
        sa.Enum(
            types.SyncStatusEnum, name="syncstatusenum", schema=config.CPO_CLIENT_SCHEMA
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
            schema=config.CPO_CLIENT_SCHEMA,
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
            schema=config.CPO_CLIENT_SCHEMA,
        ),
        nullable=False,
    )
    sync_status = sa.Column(
        sa.Enum(
            types.SyncStatusEnum, name="syncstatusenum", schema=config.CPO_CLIENT_SCHEMA
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


class CommentIntegration(RFXClientBaseModel):
    __tablename__ = "comment_integration"
    __ts_index__ = ["provider", "external_id", "external_url"]

    comment_id = sa.Column(sa.ForeignKey(Comment._id), nullable=False)
    provider = sa.Column(sa.String(100), nullable=False)  # e.g., 'linear'
    external_id = sa.Column(sa.String(255), nullable=False)
    external_url = sa.Column(sa.String(255), nullable=False)


class CommentView(RFXClientBaseModel):
    __tablename__ = "_comment"
    __table_args__ = {"schema": config.CPO_CLIENT_SCHEMA}

    master_id = sa.Column(pg.UUID)
    parent_id = sa.Column(pg.UUID)
    content = sa.Column(sa.Text)
    depth = sa.Column(sa.Integer, default=0)
    creator = sa.Column(pg.JSONB)
    organization_id = sa.Column(pg.UUID)
    resource = sa.Column(sa.String(100))
    resource_id = sa.Column(pg.UUID)
