import sqlalchemy as sa

from fluvius.data import DomainSchema, SqlaDriver, UUID_GENR
from sqlalchemy.dialects import postgresql as pg

from . import types, config


class CPOPortalConnector(SqlaDriver):
    assert config.DB_DSN, "[rfx_client.DB_DSN] not set."

    __db_dsn__ = config.DB_DSN


class CPOPortalBaseModel(CPOPortalConnector.__data_schema_base__, DomainSchema):
    __abstract__ = True
    __table_args__ = {'schema': config.CPO_PORTAL_SCHEMA}

    _realm = sa.Column(sa.String)


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
    status = sa.Column(
        sa.Enum(types.ProjectStatus, name="project_status",
                schema=config.CPO_PORTAL_SCHEMA),
        nullable=False
    )
    start_date = sa.Column(sa.DateTime(timezone=True))
    target_date = sa.Column(sa.DateTime(timezone=True))
    free_credit_applied = sa.Column(sa.Integer, default=0)
    lead_id = sa.Column(pg.UUID)  # FK to profile(_id)
    referral_code_used = sa.Column(pg.UUID)  # FK to referral_code(_id)
    status_workflow_id = sa.Column(pg.UUID)  # FK to workflow(_id)
    sync_status = sa.Column(
        sa.Enum(types.SyncStatus, name="sync_status",
                schema=config.CPO_PORTAL_SCHEMA),
        default=types.SyncStatus.PENDING
    )


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


# Project Referral Code Entity
class ProjectReferralCode(CPOPortalBaseModel):
    __tablename__ = "project-referral-code"

    code = sa.Column(sa.String(50), nullable=False, unique=True)
    valid_from = sa.Column(sa.DateTime(timezone=True), nullable=False)
    valid_until = sa.Column(sa.DateTime(timezone=True), nullable=False)
    max_uses = sa.Column(sa.Integer, nullable=False)
    current_uses = sa.Column(sa.Integer, default=0)
    discount_value = sa.Column(sa.Numeric(10, 2), nullable=False)


# Project Work Package Entity
class ProjectWorkPackage(CPOPortalBaseModel):
    __tablename__ = "project-work-package"

    project_id = sa.Column(sa.ForeignKey(Project._id), nullable=False)
    # FK to work_package(_id)
    work_package_id = sa.Column(pg.UUID, nullable=False)
    wp_code = sa.Column(sa.String(50), nullable=False)
    quantity = sa.Column(sa.Integer, nullable=False, default=1)


# Reference Tables
class RefProjectCategory(CPOPortalBaseModel):
    __tablename__ = "ref--project-category"

    code = sa.Column(sa.String(50), nullable=False,
                     unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)


class RefProjectRole(CPOPortalBaseModel):
    __tablename__ = "ref--project-role"

    code = sa.Column(sa.String(50), nullable=False,
                     unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_default = sa.Column(sa.Boolean, default=False)


# Work Package Aggregate Root
class WorkPackage(CPOPortalBaseModel):
    __tablename__ = "work-package"

    work_package_name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    # FK to ref--work-package-type
    type = sa.Column(sa.String(100), nullable=False)
    # FK to ref--work-package-complexity
    complexity_level = sa.Column(sa.String(100), nullable=False)
    credits = sa.Column(sa.Numeric(10, 2), nullable=False)
    is_active = sa.Column(sa.Boolean, default=True)
    example_description = sa.Column(sa.Text)


class RefWorkPackageType(CPOPortalBaseModel):
    __tablename__ = "ref--work-package-type"

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)


class RefWorkPackageComplexity(CPOPortalBaseModel):
    __tablename__ = "ref--work-package-complexity"

    code = sa.Column(sa.String(50), nullable=False,
                     unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)


# Ticket Aggregate Root
class Ticket(CPOPortalBaseModel):
    __tablename__ = "ticket"

    title = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    priority = sa.Column(
        sa.Enum(types.Priority, name="priority",
                schema=config.CPO_PORTAL_SCHEMA),
        nullable=False
    )
    type = sa.Column(sa.String(100), nullable=False)  # FK to ref--ticket-type
    parent_id = sa.Column(pg.UUID)  # FK to ticket(_id)
    assignee = sa.Column(pg.UUID)  # FK to profile(_id)
    status = sa.Column(sa.String(100), nullable=False)  # FK to ticekt_status
    workflow_id = sa.Column(pg.UUID)  # FK to workflow(_id)
    availability = sa.Column(
        sa.Enum(types.Availability, name="availability",
                schema=config.CPO_PORTAL_SCHEMA),
        nullable=False
    )
    sync_status = sa.Column(
        sa.Enum(types.SyncStatus, name="sync_status",
                schema=config.CPO_PORTAL_SCHEMA),
        default=types.SyncStatus.PENDING
    )


# Ticket Status Entity
class TicketStatus(CPOPortalBaseModel):
    __tablename__ = "ticket-status"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    # FK to workflow-status
    src_state = sa.Column(sa.String(100), nullable=False)
    # FK to workflow-status
    dst_state = sa.Column(sa.String(100), nullable=False)
    note = sa.Column(sa.Text)


# Ticket Comment Entity
class TicketComment(CPOPortalBaseModel):
    __tablename__ = "ticket-comment"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    comment_id = sa.Column(pg.UUID, nullable=False)  # FK to comment(_id)


# Ticket Assignee Entity
class TicketAssignee(CPOPortalBaseModel):
    __tablename__ = "ticket-assignee"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    member_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)
    role = sa.Column(sa.String(100), nullable=False)  # FK to ref--project-role

    __table_args__ = (
        sa.UniqueConstraint('ticket_id', 'member_id',
                            name='uq_ticket_assignee'),
    )


# Ticket Participants Entity
class TicketParticipants(CPOPortalBaseModel):
    __tablename__ = "ticket-participants"

    ticket_id = sa.Column(sa.ForeignKey(Ticket._id), nullable=False)
    participant_id = sa.Column(pg.UUID, nullable=False)  # FK to profile(_id)


class RefTicketType(CPOPortalBaseModel):
    __tablename__ = "ref--ticket-type"

    key = sa.Column(sa.String(50), nullable=False,
                    unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    icon_color = sa.Column(sa.String(7))  # Hex color code
    is_active = sa.Column(sa.Boolean, default=True)


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


# Tag Aggregate Root
class Tag(CPOPortalBaseModel):
    __tablename__ = "tag"

    code = sa.Column(sa.String(50), nullable=False, unique=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)
    target_resource = sa.Column(sa.String(100), nullable=False)
    target_resource_id = sa.Column(sa.String(255))

    __table_args__ = (
        sa.UniqueConstraint('code', 'target_resource',
                            'target_resource_id', name='uq_tag_target'),
    )


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

    __table_args__ = (
        sa.UniqueConstraint('entity_type', 'entity_id',
                            'provider', name='uq_integration_entity'),
    )


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
