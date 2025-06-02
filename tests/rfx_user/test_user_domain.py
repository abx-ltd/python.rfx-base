from pytest import mark
from rfx_user import UserProfileDomain

from fluvius.domain.context import DomainTransport
from fluvius.data import UUID_GENR


FIXTURE_REALM = "rfx-user-testing"
FIXTURE_USER_ID = "88212396-02c5-46ae-a2ad-f3b7eb7579c0"
FIXTURE_ORGANIZATION_ID = ""
FIXTURE_PROFILE_ID = ""
FIXTURE_DOMAIN = UserProfileDomain(None)

async def command_handler(cmd_key, payload, resource, identifier, scope={}):
    domain = FIXTURE_DOMAIN
    context = domain.setup_context(
        headers=dict(),
        transport=DomainTransport.FASTAPI,
        source="rfx-base",
        realm=FIXTURE_REALM,
        user_id=FIXTURE_USER_ID,
        organization_id=FIXTURE_ORGANIZATION_ID,
        profile_id=FIXTURE_PROFILE_ID,
    )

    command = domain.create_command(
        cmd_key,
        payload,
        aggroot=(
            resource,
            identifier,
            scope.get('domain_sid'),
            scope.get('domain_iid'),
        )
    )

    return await domain.process_command(command, context=context)

# ------------------------------
# Organization Setup
# ------------------------------
@mark.asyncio
@mark.order(1)
async def test_manage_organization():
    """Create a new organization with unique name/code"""
    org_id = UUID_GENR()
    payload = dict(
        name="org-1",
        description="org-1",
        tax_id="orgtax01",
        business_name="org-1"
    )
    await command_handler("create-organization", payload, "organization", org_id)
    await FIXTURE_DOMAIN.statemgr.fetch("organization", org_id)
    assert len(await FIXTURE_DOMAIN.statemgr.query("profile", where=dict(organization_id=org_id))) == 1

    payload.update(name="org-updated")
    await command_handler("update-organization", payload, "organization", org_id)
    item = await FIXTURE_DOMAIN.statemgr.fetch("organization", org_id)
    assert item.name == "org-updated"

    await command_handler("deactivate-organization", {}, "organization", org_id)
    item = await FIXTURE_DOMAIN.statemgr.fetch("organization", org_id)
    assert item.status.value == "INACTIVE"


@mark.asyncio
@mark.order(1.5)
async def test_manage_org_role():
    FIXTURE_ORGANIZATION_ID
    

# ------------------------------
# User Invitation Flow
# ------------------------------
@mark.asyncio
@mark.order(4)
async def test_invite_user_by_email():
    print("test_invite_user_by_email")
    """Invite a user by email with selected roles"""

@mark.asyncio
@mark.order(5)
async def test_generate_invitation_code_and_expiry():
    print("test_generate_invitation_code_and_expiry")
    """Generate unique invitation code with expiration time"""

@mark.asyncio
@mark.order(6)
async def test_prevent_duplicate_invitations():
    print("test_prevent_duplicate_invitations")
    """Prevent duplicate active invitations to same email/org"""

@mark.asyncio
@mark.order(7)
async def test_revoke_pending_invitation():
    print("test_revoke_pending_invitation")
    """Revoke an unaccepted invitation"""

@mark.asyncio
@mark.order(8)
async def test_accept_invitation_creates_profile():
    print("test_accept_invitation_creates_profile")
    """Accept invitation and convert to active profile"""


# ------------------------------
# Profile Management
# ------------------------------
@mark.asyncio
@mark.order(9)
async def test_create_profile_on_acceptance():
    print("test_create_profile_on_acceptance")
    """Accepting invitation creates profile linked to organization"""

@mark.asyncio
@mark.order(10)
async def test_assign_multiple_roles_to_profile():
    print("test_assign_multiple_roles_to_profile")
    """Assign multiple roles to a profile"""

@mark.asyncio
@mark.order(11)
async def test_revoke_role_from_profile():
    print("test_revoke_role_from_profile")
    """Remove or revoke role from profile"""

@mark.asyncio
@mark.order(12)
async def test_transition_profile_status():
    print("test_transition_profile_status")
    """Transition profile status to ACTIVE, LOCKED, INACTIVE"""

@mark.asyncio
@mark.order(13)
async def test_block_action_from_locked_or_inactive_profile():
    print("test_block_action_from_locked_or_inactive_profile")
    """Prevent actions from LOCKED or INACTIVE profile"""


# ------------------------------
# Group Context and Profile Group
# ------------------------------
@mark.asyncio
@mark.order(14)
async def test_create_group_in_org():
    print("test_create_group_in_org")
    """Create a new group within an organization"""

@mark.asyncio
@mark.order(15)
async def test_assign_profile_to_group():
    print("test_assign_profile_to_group")
    """Assign a profile to a group within the organization"""

@mark.asyncio
@mark.order(16)
async def test_remove_profile_from_group():
    print("test_remove_profile_from_group")
    """Remove a profile from a group"""

@mark.asyncio
@mark.order(17)
async def test_fetch_profiles_in_group():
    print("test_fetch_profiles_in_group")
    """Fetch all profiles assigned to a group"""

@mark.asyncio
@mark.order(18)
async def test_group_level_permission_inference():
    print("test_group_level_permission_inference")
    """Ensure group permissions are inherited or aggregated properly"""


# ------------------------------
# User Identity & Login
# ------------------------------
@mark.asyncio
@mark.order(19)
async def test_user_login_gets_access_token():
    print("test_user_login_gets_access_token")
    """User can login and retrieve access token"""

@mark.asyncio
@mark.order(20)
async def test_token_contains_profile_and_org():
    print("test_token_contains_profile_and_org")
    """Token includes current profile_id and org_id"""

@mark.asyncio
@mark.order(21)
async def test_login_blocked_when_user_deactivated():
    print("test_login_blocked_when_user_deactivated")
    """User cannot login if user is globally deactivated"""

@mark.asyncio
@mark.order(22)
async def test_login_blocked_when_profile_or_org_inactive():
    print("test_login_blocked_when_profile_or_org_inactive")
    """Login denied if profile is locked or org is inactive"""


# ------------------------------
# Authorization & Permissions
# ------------------------------
@mark.asyncio
@mark.order(23)
async def test_admin_can_create_project():
    print("test_admin_can_create_project")
    """Profile with role 'admin' can run create-project command"""

@mark.asyncio
@mark.order(24)
async def test_viewer_can_only_query_project():
    print("test_viewer_can_only_query_project")
    """Profile with role 'viewer' can only run query-project"""

@mark.asyncio
@mark.order(25)
async def test_profile_access_isolated_by_org():
    print("test_profile_access_isolated_by_org")
    """Profile in Org A cannot access resources of Org B"""

@mark.asyncio
@mark.order(26)
async def test_removed_role_blocks_action():
    print("test_removed_role_blocks_action")
    """Profile removed from role cannot access corresponding action"""


# ------------------------------
# Multi-Organization Membership
# ------------------------------
@mark.asyncio
@mark.order(27)
async def test_fetch_user_profiles_across_orgs():
    print("test_fetch_user_profiles_across_orgs")
    """Fetch all profiles for a user (across organizations)"""

@mark.asyncio
@mark.order(28)
async def test_user_has_different_roles_in_different_orgs():
    print("test_user_has_different_roles_in_different_orgs")
    """User has different roles in different organizations"""

@mark.asyncio
@mark.order(29)
async def test_deactivate_user_cascades_profiles():
    print("test_deactivate_user_cascades_profiles")
    """Deactivating user deactivates all profiles"""

@mark.asyncio
@mark.order(30)
async def test_deactivate_org_blocks_all_profiles():
    print("test_deactivate_org_blocks_all_profiles")
    """Deactivating org disables all access to profiles within"""


# ------------------------------
# Audit & History Tracking
# ------------------------------
@mark.asyncio
@mark.order(31)
async def test_record_profile_status_history():
    print("test_record_profile_status_history")
    """Record profile status history (invited → active → inactive)"""

@mark.asyncio
@mark.order(32)
async def test_record_role_assignment_logs():
    print("test_record_role_assignment_logs")
    """Record role assignment and revocation logs"""

@mark.asyncio
@mark.order(33)
async def test_track_invitation_status_transitions():
    print("test_track_invitation_status_transitions")
    """Track invitation status transitions (pending → accepted/revoked/expired)"""
