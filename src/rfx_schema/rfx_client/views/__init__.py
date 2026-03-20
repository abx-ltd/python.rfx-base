"""
RFX Client Database Views
=========================
PostgreSQL view definitions for RFX Client domain.
"""

from .comment import (
    comment_view,
    comment_attachment_view,
    comment_reaction_view,
    comment_reaction_summary_view,
)
from .credit import (
    credit_summary_view,
    organization_credit_summary_view,
    organization_weekly_credit_usage_view,
    credit_purchase_history_view,
    credit_usage_summary_view,
)


from .project import (
    project_view,
    project_credit_summary_view,
    # project_document_view,
    project_estimate_summary_view,
    document_view,
)
from .work_package import (
    fn_get_resource_json,
    work_package_view,
    project_work_package_view,
    project_work_package_relationship_view,
)
from .work_item import (
    work_item_view,
    work_item_listing_view,
    project_work_item_view,
    project_work_item_listing_view,
)
from .ticket import (
    inquiry_view,
    ticket_view,
)

from .status import (
    status_view,
)

from .supplier import (
    supplier_service_view,
)


__all__ = [
    # Comment views
    "comment_view",
    "comment_attachment_view",
    "comment_reaction_view",
    "comment_reaction_summary_view",
    # Credit views
    "credit_summary_view",
    "organization_credit_summary_view",
    "organization_weekly_credit_usage_view",
    "credit_purchase_history_view",
    "credit_usage_summary_view",
    # Project views
    "project_view",
    "project_credit_summary_view",
    "document_view",
    # Work package views
    "fn_get_resource_json",
    "work_package_view",
    "project_work_package_view",
    "project_work_package_relationship_view",
    # "work_package_credit_usage_view",
    # Work item views
    "work_item_view",
    "work_item_listing_view",
    "project_work_item_view",
    "project_work_item_listing_view",
    "project_estimate_summary_view",
    # Ticket views
    "inquiry_view",
    "ticket_view",
    # Status view
    "status_view",
    # Supplier views
    "supplier_service_view",
]
