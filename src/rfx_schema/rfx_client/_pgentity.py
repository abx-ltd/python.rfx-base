"""
RFX Client PostgreSQL View Entities
====================================
Registers database views for Alembic migrations.
"""

import os
from alembic_utils.replaceable_entity import register_entities

# Import all views from submodules
from .views import (
    # Comment views
    comment_view,
    comment_attachment_view,
    comment_reaction_view,
    comment_reaction_summary_view,
    # Credit views
    credit_summary_view,
    credit_usage_view,
    credit_purchase_history_view,
    credit_usage_summary_view,
    # Project views
    project_view,
    project_credit_summary_view,
    project_document_view,
    project_estimate_summary_view,
    work_package_view,
    project_work_package_view,
    work_package_credit_usage_view,
    # Work item views
    work_item_view,
    work_item_listing_view,
    project_work_item_view,
    project_work_item_listing_view,
    # Ticket views
    inquiry_view,
    ticket_view,
    # Organization views
    organization_credit_summary_view,
    organization_weekly_credit_usage_view,
    # Status view
    status_view,
)


def register_pg_entities(allow):
    """Register all PostgreSQL views for Alembic migrations"""

    register_entities(
        [
            # Comment views
            comment_view,
            comment_attachment_view,
            comment_reaction_view,
            comment_reaction_summary_view,
            # Credit views
            credit_summary_view,
            credit_usage_view,
            organization_credit_summary_view,
            organization_weekly_credit_usage_view,
            credit_purchase_history_view,
            credit_usage_summary_view,
            # Project views
            project_view,
            project_credit_summary_view,
            project_document_view,
            project_estimate_summary_view,
            # Work package views
            work_package_view,
            project_work_package_view,
            work_package_credit_usage_view,
            # Work item views
            work_item_view,
            work_item_listing_view,
            project_work_item_view,
            project_work_item_listing_view,
            # Ticket views
            inquiry_view,
            ticket_view,
            # Status view
            status_view,
        ]
    )


# Auto-register if environment variable is set
register_pg_entities(os.environ.get("REGISTER_PG_ENTITIES"))
