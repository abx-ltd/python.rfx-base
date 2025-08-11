from .types import Priority, SyncStatus
from .policy import CPOPortalPolicyManager
from .domain import CPOPortalDomain
from .state import CPOPortalStateManager
from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import StringField, UUIDField, BooleanField, EnumField, IntegerField, FloatField, DatetimeField, ArrayField
from . import scope
from .types import ContactMethod
from datetime import datetime
from typing import Optional


default_exclude_fields = ["realm", "deleted", "etag",
                          "created", "updated", "creator", "updater"]


class CPOPortalQueryManager(DomainQueryManager):
    __data_manager__ = CPOPortalStateManager
    __policymgr__ = CPOPortalPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = CPOPortalDomain.Meta.prefix
        tags = CPOPortalDomain.Meta.tags


resource = CPOPortalQueryManager.register_resource
endpoint = CPOPortalQueryManager.register_endpoint


class ResourceScope(BaseModel):
    resource: str
    resource_id: str


@resource('project')
class ProjectQuery(DomainQueryResource):
    """Project queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    name: str = StringField("Project Name")
    description: str = StringField("Description")
    category: str = StringField("Category")
    priority: Priority = EnumField("Priority")
    status: str = StringField("Status")
    start_date: str = DatetimeField("Start Date")
    target_date: str = DatetimeField("Target Date")
    free_credit_applied: int = IntegerField("Free Credit Applied")
    lead_id: UUID_TYPE = UUIDField("Lead ID")
    referral_code_used: UUID_TYPE = UUIDField("Referral Code Used")
    status_workflow_id: UUID_TYPE = UUIDField("Status Workflow ID")
    sync_status: SyncStatus = EnumField("Sync Status")


@resource('project-bdm-contact')
class ProjectBDMContactQuery(DomainQueryResource):
    """Project BDM contact queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        scope_required = scope.ProjectBDMContactScopeSchema

    contact_method: list[ContactMethod] = ArrayField("Contact Method")
    message: str = StringField("Message")
    meeting_time: datetime = DatetimeField("Meeting Time")
    status: str = StringField("Status")


@resource('project-milestone')
class ProjectMilestoneQuery(DomainQueryResource):
    """Project milestone queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        scope_required = scope.ProjectMilestoneScopeSchema

    name: str = StringField("Milestone Name")
    description: str = StringField("Description")
    due_date: Optional[datetime] = DatetimeField("Due Date")
    completed_at: Optional[datetime] = DatetimeField("Completed At")
    is_completed: bool = BooleanField("Is Completed")


@resource('project-estimate-summary')
class ProjectEstimateSummaryQuery(DomainQueryResource):
    """Project estimate summary queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_project-estimate-summary"

    project_id: UUID_TYPE = UUIDField("Project ID")
    architectural_credits: float = FloatField("Architectural Credits")
    development_credits: float = FloatField("Development Credits")
    operation_credits: float = FloatField("Operation Credits")
    discount_value: float = FloatField("Discount Value")
    free_credits: float = FloatField("Free Credits")
    total_credits_raw: float = FloatField("Total Credits Raw")
    total_credits_after_discount: float = FloatField(
        "Total Credits After Discount")
    total_cost: float = FloatField("Total Cost")


@resource('work-item')
class WorkItemDetailQuery(DomainQueryResource):
    """Work item detail queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    type: str = StringField("Type")
    name: str = StringField("Name")
    description: str = StringField("Description")
    price_unit: float = FloatField("Price Unit")
    credit_per_unit: float = FloatField("Credit Per Unit")
    estimate: str = StringField("Estimate")


@resource('work-item-listing')
class WorkItemListingQuery(DomainQueryResource):
    """Work item listing queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_work-item-listing"

        scope_required = scope.WorkItemListingScopeSchema

    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
    work_item_id: UUID_TYPE = UUIDField("Work Item ID")
    custom_name: str = StringField("Custom Name")
    custom_description: str = StringField("Custom Description")
    custom_price_unit: float = FloatField("Custom Price Unit")
    custom_credit_per_unit: float = FloatField("Custom Credit Per Unit")
    work_item_name: str = StringField("Work Item Name")
    work_item_description: str = StringField("Work Item Description")
    price_unit: float = FloatField("Price Unit")
    credit_per_unit: float = FloatField("Credit Per Unit")
    work_item_type_code: str = StringField("Work Item Type Code")
    total_credits_for_item: float = FloatField("Total Credits For Item")
    estimated_cost_for_item: float = FloatField("Estimated Cost For Item")
    estimate: str = StringField("Estimate")


@resource('work-package')
class WorkPackageQuery(DomainQueryResource):
    """Work package queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "_work-package-detail"

    work_package_name: str = StringField("Work Package Name")
    description: str = StringField("Description")
    example_description: str = StringField("Example Description")
    is_custom: bool = BooleanField("Is Custom")
    complexity_level: int = IntegerField("Complexity Level")
    estimate: str = StringField("Estimate")
    type_list: list[str] = ArrayField("Type List")
    credits: float = FloatField("Credits")
    architectural_credits: float = FloatField("Architectural Credits")
    development_credits: float = FloatField("Development Credits")
    operation_credits: float = FloatField("Operation Credits")
    upfront_cost: float = FloatField("Upfront Cost")
    monthly_cost: float = FloatField("Monthly Cost")


# Reference Queries
@resource('project-category')
class RefProjectCategoryQuery(DomainQueryResource):
    """Project category reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--project-category"

    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")


@resource('project-role')
class RefProjectRoleQuery(DomainQueryResource):
    """Project role reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--project-role"

    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_default: bool = BooleanField("Is Default")
