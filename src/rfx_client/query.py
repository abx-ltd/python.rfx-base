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


# @resource('project-member')
# class ProjectMemberQuery(DomainQueryResource):
#     """Project member queries"""

#     class Meta(DomainQueryResource.Meta):
#         include_all = True
#         allow_item_view = True
#         allow_list_view = True
#         allow_meta_view = True

#     project_id: UUID_TYPE = UUIDField("Project ID")
#     member_id: UUID_TYPE = UUIDField("Member ID")
#     role: str = StringField("Role")
#     permission: str = StringField("Permission")


# @resource('project-work-package')
# class ProjectWorkPackageQuery(DomainQueryResource):
#     """Project work package queries"""

#     class Meta(DomainQueryResource.Meta):
#         include_all = True
#         allow_item_view = True
#         allow_list_view = True
#         allow_meta_view = True

#     project_id: UUID_TYPE = UUIDField("Project ID")
#     work_package_id: UUID_TYPE = UUIDField("Work Package ID")
#     wp_code: str = StringField("Work Package Code")
#     quantity: int = IntegerField("Quantity")


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
    work_item_name: str = StringField("Work Item Name")
    work_item_description: str = StringField("Work Item Description")
    work_item_type_code: str = StringField("Work Item Type Code")
    work_item_type_name: str = StringField("Work Item Type Name")


# @resource('project-status')
# class ProjectStatusQuery(DomainQueryResource):
#     """Project status queries"""

#     class Meta(DomainQueryResource.Meta):
#         include_all = True
#         allow_item_view = True
#         allow_list_view = True
#         allow_meta_view = True

#     project_id: UUID_TYPE = UUIDField("Project ID")
#     src_state: str = StringField("Source State")
#     dst_state: str = StringField("Destination State")
#     note: str = StringField("Note")

# # Work Package Queries


# @resource('work-package')
# class WorkPackageQuery(DomainQueryResource):
#     """Work package queries"""

#     class Meta(DomainQueryResource.Meta):
#         include_all = True
#         allow_item_view = True
#         allow_list_view = True
#         allow_meta_view = True

#     work_package_name: str = StringField("Work Package Name")
#     type: str = StringField("Type")
#     complexity_level: str = StringField("Complexity Level")
#     credits: float = FloatField("Credits")
#     is_custom: bool = BooleanField("Is Custom")


@resource('work-package-type')
class RefWorkPackageTypeQuery(DomainQueryResource):
    """Work package type reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--work-package-type"


@resource('work-package-complexity')
class RefWorkPackageComplexityQuery(DomainQueryResource):
    """Work package complexity reference queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "ref--work-package-complexity"

    code: str = StringField("Code")
    name: str = StringField("Name")


@resource('work-package')
class WorkPackageQuery(DomainQueryResource):
    """Work package queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        backend_model = "_work-package-detail"

    work_package_id: UUID_TYPE = UUIDField("Work Package ID")
    work_package_name: str = StringField("Work Package Name")
    type_list: list[str] = ArrayField("Type List")


# Integration Queries
# @resource('integration')
# class IntegrationQuery(DomainQueryResource):
#     """Integration queries"""

#     class Meta(DomainQueryResource.Meta):
#         include_all = True
#         allow_item_view = True
#         allow_list_view = True
#         allow_meta_view = True

#     entity_type: str = StringField("Entity Type")
#     entity_id: UUID_TYPE = UUIDField("Entity ID")
#     provider: str = StringField("Provider")
#     external_id: str = StringField("External ID")
#     external_url: str = StringField("External URL")
#     status: SyncStatus = EnumField("Status")


# Notification Queries
# @resource('notification')
# class NotificationQuery(DomainQueryResource):
#     """Notification queries"""

#     class Meta(DomainQueryResource.Meta):
#         include_all = True
#         allow_item_view = True
#         allow_list_view = True
#         allow_meta_view = True

#     user_id: UUID_TYPE = UUIDField("User ID")
#     source_entity_type: str = StringField("Source Entity Type")
#     source_entity_id: UUID_TYPE = UUIDField("Source Entity ID")
#     message: str = StringField("Message")
#     type: str = StringField("Type")
#     is_read: bool = BooleanField("Is Read")


# @resource('notification-type')
# class RefNotificationTypeQuery(DomainQueryResource):
#     """Notification type reference queries"""

#     class Meta(DomainQueryResource.Meta):
#         include_all = True
#         allow_item_view = True
#         allow_list_view = True
#         allow_meta_view = True
#         backend_model = "ref--notification-type"

#     name: str = StringField("Name")
#     description: str = StringField("Description")
#     is_active: bool = BooleanField("Is Active")


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

    code: str = StringField("Code")
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

    code: str = StringField("Code")
    name: str = StringField("Name")
    description: str = StringField("Description")
    is_default: bool = BooleanField("Is Default")
