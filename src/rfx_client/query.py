from .types import PriorityEnum, SyncStatusEnum, AvailabilityEnum
from .policy import RFXClientPolicyManager
from .domain import RFXClientDomain
from .state import RFXClientStateManager
from pydantic import BaseModel
from fluvius.data import UUID_TYPE
from fluvius.query import DomainQueryManager, DomainQueryResource
from fluvius.query.field import (
    StringField,
    UUIDField,
    BooleanField,
    EnumField,
    IntegerField,
    FloatField,
    DatetimeField,
    ArrayField,
    DictField,
)
from . import scope
from .types import ContactMethodEnum
from datetime import datetime
from typing import Optional


default_exclude_fields = [
    "realm",
    "deleted",
    "etag",
    "created",
    "updated",
    "creator",
    "updater",
]


class RFXClientQueryManager(DomainQueryManager):
    __data_manager__ = RFXClientStateManager
    __policymgr__ = RFXClientPolicyManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXClientDomain.Meta.prefix
        tags = RFXClientDomain.Meta.tags


resource = RFXClientQueryManager.register_resource
endpoint = RFXClientQueryManager.register_endpoint


class ResourceScope(BaseModel):
    resource: str
    resource_id: str


# class ProjectScopeSchema(BaseModel):
#     project_id: str = ""


@resource("estimator")
class ProjectDraftQuery(DomainQueryResource):
    """Project draft queries"""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {"members.ov": [profile_id], "status": "DRAFT"}

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "_project"
        policy_required = "id"

    name: str = StringField("Project Name")
    description: str = StringField("Description")
    category: str = StringField("Category")
    priority: PriorityEnum = EnumField("Priority")
    start_date: str = DatetimeField("Start Date")
    target_date: str = DatetimeField("Target Date")
    free_credit_applied: int = IntegerField("Free Credit Applied")
    referral_code_used: UUID_TYPE = UUIDField("Referral Code Used")
    members: list[UUID_TYPE] = ArrayField("Members")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


# Project Queries
@resource("project")
class ProjectQuery(DomainQueryResource):
    """Project queries"""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {"members.ov": [profile_id], "status": "ACTIVE"}

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "_project"
        policy_required = "id"

    name: str = StringField("Project Name")
    description: str = StringField("Description")
    category: str = StringField("Category")
    priority: PriorityEnum = EnumField("Priority")
    status: str = StringField("Status")
    start_date: str = DatetimeField("Start Date")
    target_date: str = DatetimeField("Target Date")
    free_credit_applied: int = IntegerField("Free Credit Applied")
    referral_code_used: UUID_TYPE = UUIDField("Referral Code Used")
    sync_status: SyncStatusEnum = EnumField("Sync Status")
    members: list[UUID_TYPE] = ArrayField("Members")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    total_credits: float = FloatField("Total Credits")
    used_credits: float = FloatField("Used Credits")


@resource("project-bdm-contact")
class ProjectBDMContactQuery(DomainQueryResource):
    """Project BDM contact queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        policy_required = "project_id"
        scope_required = scope.ProjectBDMContactScopeSchema

    contact_method: list[ContactMethodEnum] = ArrayField("Contact Method")
    message: str = StringField("Message")
    meeting_time: datetime = DatetimeField("Meeting Time")
    status: str = StringField("Status")


@resource("project-milestone")
class ProjectMilestoneQuery(DomainQueryResource):
    """Project milestone queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        policy_required = "project_id"
        scope_required = scope.ProjectMilestoneScopeSchema

    name: str = StringField("Milestone Name")
    description: str = StringField("Description")
    due_date: Optional[datetime] = DatetimeField("Due Date")
    completed_at: Optional[datetime] = DatetimeField("Completed At")
    is_completed: bool = BooleanField("Is Completed")
    project_id: UUID_TYPE = UUIDField("Project ID")


@resource("project-estimate-summary")
class ProjectEstimateSummaryQuery(DomainQueryResource):
    """Project estimate summary queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_project_estimate_summary"
        policy_required = "id"

    architectural_credits: float = FloatField("Architectural Credits")
    development_credits: float = FloatField("Development Credits")
    operation_credits: float = FloatField("Operation Credits")
    discount_value: float = FloatField("Discount Value")
    free_credits: float = FloatField("Free Credits")
    total_credits_raw: float = FloatField("Total Credits Raw")
    total_credits_after_discount: float = FloatField("Total Credits After Discount")
    total_cost: float = FloatField("Total Cost")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


@resource("project-category")
class RefProjectCategoryQuery(DomainQueryResource):
    """Project category reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "ref__project_category"

    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")


@resource("project-role")
class RefProjectRoleQuery(DomainQueryResource):
    """Project role reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "ref__project_role"

    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_default: bool = BooleanField("Is Default")


@resource("project-work-package")
class ProjectWorkPackageQuery(DomainQueryResource):
    """Project work package queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "_project_work_package"
        scope_required = scope.ProjectWorkPackageScopeSchema
        policy_required = "project_id"

    project_id: UUID_TYPE = UUIDField("Project ID")
    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
    work_package_name: str = StringField("Work Package Name")
    work_package_description: str = StringField("Work Package Description")
    work_package_example_description: str = StringField(
        "Work Package Example Description"
    )
    work_package_complexity_level: int = IntegerField("Work Package Complexity Level")
    work_package_estimate: str = StringField("Work Package Estimate")
    work_package_is_custom: bool = BooleanField("Work Package Is Custom")
    quantity: int = IntegerField("Quantity")
    type_list: list[str] = ArrayField("Type List")
    work_item_count: int = IntegerField("Work Item Count")
    credits: float = FloatField("Credits")
    architectural_credits: float = FloatField("Architectural Credits")
    development_credits: float = FloatField("Development Credits")
    operation_credits: float = FloatField("Operation Credits")
    upfront_cost: float = FloatField("Upfront Cost")
    monthly_cost: float = FloatField("Monthly Cost")
    total_deliverables: int = IntegerField("Total Deliverables")


@resource("project-work-item")
class ProjectWorkItemDetailQuery(DomainQueryResource):
    """Work item detail queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "_project_work_item"
        allow_text_search = True

    type: str = StringField("Type")
    name: str = StringField("Name")
    description: str = StringField("Description")
    price_unit: float = FloatField("Price Unit")
    credit_per_unit: float = FloatField("Credit Per Unit")
    estimate: str = StringField("Estimate")
    type_alias: str = StringField("Type Alias")


@resource("project-work-item-listing")
class ProjectWorkItemListingQuery(DomainQueryResource):
    """Work item listing queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "_project_work_item_listing"
        scope_required = scope.ProjectWorkItemListingScopeSchema

    project_work_package_id: UUID_TYPE = UUIDField("Project Work Package ID")
    project_work_item_id: UUID_TYPE = UUIDField("Project Work Item ID")
    status: str = StringField("Status")
    project_work_item_name: str = StringField("Project Work Item Name")
    project_work_item_description: str = StringField("Project Work Item Description")
    price_unit: float = FloatField("Price Unit")
    credit_per_unit: float = FloatField("Credit Per Unit")
    project_work_item_type_code: str = StringField("Project Work Item Type Code")
    project_work_item_type_alias: str = StringField("Project Work Item Type Alias")
    total_credits_for_item: float = FloatField("Total Credits For Item")
    estimated_cost_for_item: float = FloatField("Estimated Cost For Item")
    estimate: str = StringField("Estimate")


# Work Item Queries


@resource("work-item-type")
class WorkItemTypeQuery(DomainQueryResource):
    """Work item type queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "ref__work_item_type"

    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    alias: str = StringField("Alias")


@resource("work-item")
class WorkItemDetailQuery(DomainQueryResource):
    """Work item detail queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "_work_item"

    type: str = StringField("Type")
    name: str = StringField("Name")
    description: str = StringField("Description")
    price_unit: float = FloatField("Price Unit")
    credit_per_unit: float = FloatField("Credit Per Unit")
    estimate: str = StringField("Estimate")
    type_alias: str = StringField("Type Alias")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


@resource("work-item-listing")
class WorkItemListingQuery(DomainQueryResource):
    """Work item listing queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "_work_item_listing"

        scope_required = scope.WorkItemListingScopeSchema

    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
    work_item_id: UUID_TYPE = UUIDField("Work Item ID")
    work_item_name: str = StringField("Work Item Name")
    work_item_description: str = StringField("Work Item Description")
    price_unit: float = FloatField("Price Unit")
    credit_per_unit: float = FloatField("Credit Per Unit")
    work_item_type_code: str = StringField("Work Item Type Code")
    work_item_type_alias: str = StringField("Work Item Type Alias")
    total_credits_for_item: float = FloatField("Total Credits For Item")
    estimated_cost_for_item: float = FloatField("Estimated Cost For Item")
    estimate: str = StringField("Estimate")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


@resource("work-item-deliverable")
class WorkItemDeliverableQuery(DomainQueryResource):
    """Work item deliverable queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        scope_required = scope.WorkItemDeliverableScopeSchema

    name: str = StringField("Name")
    description: str = StringField("Description")
    work_item_id: UUID_TYPE = UUIDField("Work Item ID")


# Work Package Queries


@resource("work-package")
class WorkPackageQuery(DomainQueryResource):
    """work package queries"""

    @classmethod
    def base_query(cls, context, scope):
        return {
            ".or": [
                {"organization_id": None},
                {"organization_id": context.organization._id},
            ]
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True
        backend_model = "_work_package"

    work_package_name: str = StringField("Work Package Name")
    description: str = StringField("Description")
    example_description: str = StringField("Example Description")
    complexity_level: int = IntegerField("Complexity Level")
    estimate: str = StringField("Estimate")
    type_list: list[str] = ArrayField("Type List")
    credits: float = FloatField("Credits")
    architectural_credits: float = FloatField("Architectural Credits")
    development_credits: float = FloatField("Development Credits")
    operation_credits: float = FloatField("Operation Credits")
    upfront_cost: float = FloatField("Upfront Cost")
    monthly_cost: float = FloatField("Monthly Cost")
    work_item_count: int = IntegerField("Work Item Count")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    is_custom: bool = BooleanField("Is Custom")


@resource("promotion")
class PromotionQuery(DomainQueryResource):
    """Promotion queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "promotion"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

    code: str = StringField("Code")
    valid_from: datetime = DatetimeField("Valid From")
    valid_until: datetime = DatetimeField("Valid Until")
    max_uses: int = IntegerField("Max Uses")
    current_uses: int = IntegerField("Current Uses")
    discount_value: float = FloatField("Discount Value")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


# ======== Ticket Query===========
@resource("inquiry")
class InquiryQuery(DomainQueryResource):
    """Inquiry listing queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "ticket"
        include_all = True
        allow_list_view = True
        allow_item_view = True
        allow_meta_view = True

        backend_model = "_inquiry"
        policy_required = "id"

    type: str = StringField("Type")
    type_icon_color: str = StringField("Type Icon Color")
    title: str = StringField("Title")
    tag_names: list[str] = ArrayField("Tag Names")
    availability: AvailabilityEnum = EnumField("Availability")
    activity: datetime = DatetimeField("Activity")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    status: str = StringField("Status")
    description: str = StringField("Description")


# Ticket Queries


@resource("ticket")
class TicketQuery(DomainQueryResource):
    """Ticket queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "ticket"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_ticket"
        scope_required = scope.TicketScopeSchema
        policy_required = "id"

    project_id: UUID_TYPE = UUIDField("Project ID")
    title: str = StringField("Title")
    description: str = StringField("Description")
    priority: PriorityEnum = EnumField("Priority")
    type: str = StringField("Type")
    parent_id: UUID_TYPE = UUIDField("Parent ID")
    assignee: UUID_TYPE = UUIDField("Assignee")
    status: str = StringField("Status")
    availability: AvailabilityEnum = EnumField("Availability")
    sync_status: SyncStatusEnum = EnumField("Sync Status")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


@resource("ticket-type")
class RefTicketTypeQuery(DomainQueryResource):
    """Ticket type reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        excluded_fields = default_exclude_fields
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref__ticket_type"

    name: str = StringField("Name")
    description: str = StringField("Description")
    icon_color: str = StringField("Icon Color")
    is_active: bool = BooleanField("Is Active")
    is_inquiry: bool = BooleanField("Is Inquiry")


# Tag Queries
@resource("tag")
class TagQuery(DomainQueryResource):
    """Tag queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "tag"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    key: str = StringField("Key")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_active: bool = BooleanField("Is Active")
    target_resource: str = StringField("Target Resource")
    target_resource_id: str = StringField("Target Resource ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")


@resource("comment")
class CommentQuery(DomainQueryResource):
    """Comment queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment"
        scope_required = scope.CommentScopeSchema

    master_id: UUID_TYPE = UUIDField("Master ID")
    parent_id: UUID_TYPE = UUIDField("Parent ID")
    depth: int = IntegerField("Depth")
    content: str = StringField("Content")
    creator: dict = DictField("Creator")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    resource: str = StringField("Resource Type")
    resource_id: UUID_TYPE = UUIDField("Resource ID")
    source: str = StringField("Source")


@resource("comment-attachment")
class CommentAttachmentQuery(DomainQueryResource):
    """Comment attachment queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "commment_attachment"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment_attachment"
        scope_required = scope.CommentAttachmentScopeSchema

    comment_id: UUID_TYPE = UUIDField("Comment ID", filterable=True)
    media_entry_id: UUID_TYPE = UUIDField("Media Entry ID", filterable=True)
    attachment_type: str = StringField("Attachment Type", filterable=True)
    caption: str = StringField("Caption")
    display_order: int = IntegerField("Display Order")
    is_primary: bool = BooleanField("Is Primary")


@resource("comment-reaction")
class CommentReactionQuery(DomainQueryResource):
    """Comment reaction queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment_reaction"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment_reaction"
        scope_required = scope.CommentReactionScopeSchema

    comment_id: UUID_TYPE = UUIDField("Comment ID", filterable=True)
    user_id: UUID_TYPE = UUIDField("User ID", filterable=True)
    reaction_type: str = StringField("Reaction Type", filterable=True)


@resource("comment-reaction-summary")
class CommentReactionSummaryQuery(DomainQueryResource):
    """Comment Reaction Summary queries"""

    class Meta(DomainQueryResource.Meta):
        resource = "comment-reaction-summary"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_comment_reaction_summary"
        scope_required = scope.CommentReactionScopeSchema

    comment_id: UUID_TYPE = UUIDField("Comment ID", filterable=True)
    reaction_type: str = StringField("Reaction Type", filterable=True)
    reaction_count: int = IntegerField("Reaction Count")
    users: dict = DictField("Users")


@resource("credit-summary")
class CreditSummaryQuery(DomainQueryResource):
    """Credit summary for organization dashboard"""

    class Meta(DomainQueryResource.Meta):
        resource = "credit-summary"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_credit_summary"
        # scope_required = scope.OrganizationScopeSchema
        # policy_required = "organization_id"

    organization_id: UUID_TYPE = UUIDField("Organization ID")
    current_ar_credits: float = FloatField("Current AR Credits")
    current_de_credits: float = FloatField("Current DE Credits")
    current_op_credits: float = FloatField("Current OP Credits")
    current_total_credits: float = FloatField("Current Total Credits")
    total_purchased_credits: float = FloatField("Total Purchased Credits")
    remaining_credits: float = FloatField("Remaining Credits")
    remaining_percentage: float = FloatField("Remaining Percentage")
    avg_daily_usage: float = FloatField("Average Daily Usage")
    avg_weekly_usage: float = FloatField("Average Weekly Usage")
    days_until_depleted: int = IntegerField("Days Until Depleted")
    month_purchased: float = FloatField("Month Purchased")
    month_used: float = FloatField("Month Used")
    last_purchase_date: datetime = DatetimeField("Last Purchase Date")
    last_usage_date: datetime = DatetimeField("Last Usage Date")


@resource("work-package-credit-usage")
class WorkPackageCreditUsageQuery(DomainQueryResource):
    """Credit usage breakdown by work package"""

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_work_package_credit_usage"
        scope_required = scope.ProjectWorkPackageScopeSchema
        policy_required = "project_id"

    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
    project_id: UUID_TYPE = UUIDField("Project ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    work_package_name: str = StringField("Work Package Name")
    estimated_ar_credits: float = FloatField("Estimated AR Credits")
    estimated_de_credits: float = FloatField("Estimated DE Credits")
    estimated_op_credits: float = FloatField("Estimated OP Credits")
    estimated_total_credits: float = FloatField("Estimated Total Credits")
    actual_ar_credits: float = FloatField("Actual AR Credits")
    actual_de_credits: float = FloatField("Actual DE Credits")
    actual_op_credits: float = FloatField("Actual OP Credits")
    actual_total_credits: float = FloatField("Actual Total Credits")
    variance_ar: float = FloatField("Variance AR")
    variance_de: float = FloatField("Variance DE")
    variance_op: float = FloatField("Variance OP")
    variance_total: float = FloatField("Variance Total")
    variance_percentage: float = FloatField("Variance Percentage")
    completion_percentage: float = FloatField("Completion Percentage")
    credits_remaining: float = FloatField("Credits Remaining")
    total_work_items: int = IntegerField("Total Work Items")
    completed_work_items: int = IntegerField("Completed Work Items")
    status: str = StringField("Status")


@resource("credit-purchase-history")
class CreditPurchaseHistoryQuery(DomainQueryResource):
    """Credit purchase transaction history"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_credit_purchase_history"
        policy_required = "organization_id"

    purchase_id: UUID_TYPE = UUIDField("Purchase ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    purchase_date: datetime = DatetimeField("Purchase Date")
    ar_credits: float = FloatField("AR Credits")
    de_credits: float = FloatField("DE Credits")
    op_credits: float = FloatField("OP Credits")
    total_credits: float = FloatField("Total Credits")
    amount: float = FloatField("Amount")
    currency: str = StringField("Currency")
    payment_method: str = StringField("Payment Method")
    transaction_id: str = StringField("Transaction ID")
    invoice_number: str = StringField("Invoice Number")
    discount_code: str = StringField("Discount Code")
    discount_amount: float = FloatField("Discount Amount")
    final_amount: float = FloatField("Final Amount")
    status: str = StringField("Status")
    package_name: str = StringField("Package Name")
    package_code: str = StringField("Package Code")
    purchased_by: UUID_TYPE = UUIDField("Purchased By")
    purchaser_name: str = StringField("Purchaser Name")
    purchaser_email: str = StringField("Purchaser Email")
    created_at: datetime = DatetimeField("Created At")
    completed_date: datetime = DatetimeField("Completed Date")


@resource("credit-package")
class CreditPackageQuery(DomainQueryResource):
    """Available credit packages for purchase"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

    package_name: str = StringField("Package Name")
    package_code: str = StringField("Package Code")
    ar_credits: float = FloatField("AR Credits")
    de_credits: float = FloatField("DE Credits")
    op_credits: float = FloatField("OP Credits")
    total_credits: float = FloatField("Total Credits")
    price: float = FloatField("Price")
    currency: str = StringField("Currency")
    description: str = StringField("Description")
    features: dict = DictField("Features")
    is_active: bool = BooleanField("Is Active")
    sort_order: int = IntegerField("Sort Order")


@resource("credit-balance")
class CreditBalanceQuery(DomainQueryResource):
    """Current credit balance for organization"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = False
        allow_meta_view = False

        policy_required = "organization_id"

    organization_id: UUID_TYPE = UUIDField("Organization ID")
    ar_credits: float = FloatField("AR Credits")
    de_credits: float = FloatField("DE Credits")
    op_credits: float = FloatField("OP Credits")
    total_credits: float = FloatField("Total Credits")
    total_purchased_credits: float = FloatField("Total Purchased Credits")
    total_used: float = FloatField("Total Used")
    total_refunded_credits: float = FloatField("Total Refunded Credits")
    avg_daily_usage: float = FloatField("Average Daily Usage")
    avg_weekly_usage: float = FloatField("Average Weekly Usage")
    estimated_depletion_date: datetime = DatetimeField("Estimated Depletion Date")
    days_until_depleted: int = IntegerField("Days Until Depleted")
    is_low_balance: bool = BooleanField("Is Low Balance")
    low_balance_threshold: float = FloatField("Low Balance Threshold")
    last_purchase_date: datetime = DatetimeField("Last Purchase Date")
    last_usage_date: datetime = DatetimeField("Last Usage Date")
    last_refund_date: datetime = DatetimeField("Last Refund Date")


@resource("credit-usage-log")
class CreditUsageLogQuery(DomainQueryResource):
    """Detailed credit usage transaction log"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        policy_required = "organization_id"

    organization_id: UUID_TYPE = UUIDField("Organization ID")
    project_id: UUID_TYPE = UUIDField("Project ID")
    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
    work_item_id: UUID_TYPE = UUIDField("Work Item ID")
    work_type: str = StringField("Work Type")
    credits_used: float = FloatField("Credits Used")
    credit_per_unit: float = FloatField("Credit Per Unit")
    units_consumed: float = FloatField("Units Consumed")
    usage_date: datetime = DatetimeField("Usage Date")
    used_by: UUID_TYPE = UUIDField("Used By")
    work_item_name: str = StringField("Work Item Name")
    work_package_name: str = StringField("Work Package Name")
    project_name: str = StringField("Project Name")
    used_by_name: str = StringField("Used By Name")
    used_by_email: str = StringField("Used By Email")
    description: str = StringField("Description")
    is_refunded: bool = BooleanField("Is Refunded")
    refund_date: datetime = DatetimeField("Refund Date")
    refund_reason: str = StringField("Refund Reason")
    refunded_credits: float = FloatField("Refunded Credits")


@resource("organization-credit-summary")
class OrganizationCreditSummaryQuery(DomainQueryResource):
    """Organization credit overview with breakdown by type (AR/DE/OP)"""

    @classmethod
    def base_query(cls, context, scope):
        return {"organization_id": context.organization._id}

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = False
        allow_list_view = True
        allow_meta_view = False

        backend_model = "_organization_credit_summary"

    organization_id: UUID_TYPE = UUIDField("Organization ID")

    total_credits: float = FloatField("Total Credits Balance")
    total_purchased_credits: float = FloatField("Total Purchased Credits")
    total_allocated: float = FloatField("Total Allocated to Projects")
    total_used: float = FloatField("Total Used (DONE WPs)")
    total_available: float = FloatField("Total Available")

    ar_credits_balance: float = FloatField("AR Credits Balance")
    ar_credits_allocated: float = FloatField("AR Credits Allocated")
    ar_credits_used: float = FloatField("AR Credits Used")
    ar_credits_available: float = FloatField("AR Credits Available")

    de_credits_balance: float = FloatField("DE Credits Balance")
    de_credits_allocated: float = FloatField("DE Credits Allocated")
    de_credits_used: float = FloatField("DE Credits Used")
    de_credits_available: float = FloatField("DE Credits Available")

    op_credits_balance: float = FloatField("OP Credits Balance")
    op_credits_allocated: float = FloatField("OP Credits Allocated")
    op_credits_used: float = FloatField("OP Credits Used")
    op_credits_available: float = FloatField("OP Credits Available")

    allocation_percentage: float = FloatField("Allocation Percentage")
    completion_percentage: float = FloatField("Completion Percentage")

    total_projects: int = IntegerField("Total Projects")
    active_projects: int = IntegerField("Active Projects")

    is_low_balance: bool = BooleanField("Is Low Balance")
    low_balance_threshold: float = FloatField("Low Balance Threshold")


@resource("project-credit-summary")
class ProjectCreditSummaryQuery(DomainQueryResource):
    """Project credit summary with completion tracking"""

    @classmethod
    def base_query(cls, context, scope):
        return {"organization_id": context.organization._id}

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "_project_credit_summary"

    # Project info
    project_id: UUID_TYPE = UUIDField("Project ID")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    project_name: str = StringField("Project Name")
    project_status: str = StringField("Project Status")

    # Credits
    total_credits: float = FloatField("Total Credits (Estimated)")
    credit_used: float = FloatField("Credit Used (DONE WPs)")
    actual_total_credits: float = FloatField("Actual Total Credits (from log)")
    credits_remaining: float = FloatField("Credits Remaining")

    # Progress
    completion_percentage: float = FloatField("Completion Percentage")

    # Work Package Stats
    total_work_packages: int = IntegerField("Total Work Packages")
    completed_work_packages: int = IntegerField("Completed Work Packages")

    # Work Item Count
    total_work_items: int = IntegerField("Total Work Items")


@resource("project-detail")
class ProjectQueryDetail(DomainQueryResource):
    """Project queries"""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {"members.ov": [profile_id], "status": "ACTIVE"}

    class Meta(DomainQueryResource.Meta):
        resource = "project"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "_project_detail"
        # policy_required = "id"

    name: str = StringField("Project Name")
    description: str = StringField("Description")
    category: str = StringField("Category")
    priority: PriorityEnum = EnumField("Priority")
    status: str = StringField("Status")
    start_date: str = DatetimeField("Start Date")
    target_date: str = DatetimeField("Target Date")
    free_credit_applied: int = IntegerField("Free Credit Applied")
    referral_code_used: UUID_TYPE = UUIDField("Referral Code Used")
    sync_status: SyncStatusEnum = EnumField("Sync Status")
    members: list[UUID_TYPE] = ArrayField("Members")
    organization_id: UUID_TYPE = UUIDField("Organization ID")
    total_credits: float = FloatField("Total Credits")
    used_credits: float = FloatField("Used Credits")


@resource("organization-weekly-credit-usage")
class OrganizationWeeklyCreditUsageQuery(DomainQueryResource):
    """
    Organization Weekly Credit Usage Query

    Theo dõi credit usage theo tuần:
    - Week number (relative to first project start date)
    - Credits breakdown by type (AR/DE/OP)
    - Work packages completed per week
    - Usage trends over time
    """

    @classmethod
    def base_query(cls, context, scope):
        """Filter by organization from context"""
        return {"organization_id": context.organization._id}

    class Meta(DomainQueryResource.Meta):
        resource = "organization-weekly-credit-usage"
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "_organization_weekly_credit_usage"

    # Organization
    organization_id: UUID_TYPE = UUIDField("Organization ID", filterable=True)

    # Week Information
    week_number: int = IntegerField("Week Number", filterable=True, sortable=True)
    week_label: str = StringField("Week Label")  # e.g., "Week 1", "Week 2"

    # Credit Breakdown
    total_credits: float = FloatField("Total Credits", sortable=True)
    ar_credits: float = FloatField("Architecture Credits", sortable=True)
    de_credits: float = FloatField("Development Credits", sortable=True)
    op_credits: float = FloatField("Operation Credits", sortable=True)

    # Work Package Stats
    work_packages_completed: int = IntegerField(
        "Work Packages Completed", sortable=True
    )


@resource("document")
class DocumentQuery(DomainQueryResource):
    """Global organization document queries"""

    @classmethod
    def base_query(cls, context, scope):
        """Filter by organization"""
        return {"organization_id": context.organization._id}

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_list_view = True
        allow_item_view = True
        allow_meta_view = True
        backend_model = "_document"

    document_name: str = StringField("Document Name")
    description: str = StringField("Description")
    doc_type: str = StringField("Document Type")
    file_size: int = IntegerField("File Size")
    status: str = StringField("Status")

    organization_id: UUID_TYPE = UUIDField("Organization ID")

    media_entry_id: UUID_TYPE = UUIDField("Media Entry ID")
    filename: str = StringField("Filename")
    filemime: str = StringField("MIME Type")
    cdn_url: str = StringField("CDN URL")
    file_length: int = IntegerField("File Length")

    created_by: dict = DictField("Created By")

    participants: list = ArrayField("Participants")
    participant_count: int = IntegerField("Participant Count")

    activity: datetime = DatetimeField("Last Activity")
    created: datetime = DatetimeField("Created At")
    updated: datetime = DatetimeField("Updated At")
