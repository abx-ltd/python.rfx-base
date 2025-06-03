import pytest
from pytest import mark
from rfx_user import UserProfileDomain
from fluvius.domain.context import DomainTransport
from fluvius.data import UUID_GENR


FIXTURE_REALM = "rfx-user-testing"
FIXTURE_USER_ID = "88212396-02c5-46ae-a2ad-f3b7eb7579c0"
FIXTURE_ORGANIZATION_ID = "d36d4aac-e224-488a-a801-83fedcc2ab39"
FIXTURE_PROFILE_ID = "3a93d8ad-23ad-4457-85c8-9e6cfcb1d6f4"

async def command_handler(domain, cmd_key, payload, resource, identifier, scope={}, context={}):
    _context = dict(
        headers=dict(),
        transport=DomainTransport.FASTAPI,
        source="rfx-base",
        realm=FIXTURE_REALM,
        user_id=FIXTURE_USER_ID,
        organization_id=FIXTURE_ORGANIZATION_ID,
        profile_id=FIXTURE_PROFILE_ID
    )
    if context:
        _context.update(**context)

    ctx = domain.setup_context(**_context)

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

    return await domain.process_command(command, context=ctx)


@pytest.fixture
def domain():
    return UserProfileDomain(None)

# ------------------------------
# Organization Setup
# ------------------------------
@mark.asyncio
@mark.order(1)
async def test_organization_context(domain):
    """ Create a new organization with unique name/code """
    org_id = UUID_GENR()
    payload = dict(name="org-1", description="org-1", tax_id="orgtax01", business_name="org-1")
    
    await command_handler(domain, "create-organization", payload, "organization", org_id)
    await command_handler(domain, "update-organization", payload | {"name": "org-updated"}, "organization", org_id)
    await command_handler(domain, "deactivate-organization", {}, "organization", org_id)
    
    item = await domain.statemgr.fetch("organization", org_id)
    assert item.status.value == "DEACTIVATED"
    assert item.name == "org-updated"

@mark.asyncio
@mark.order(2)
async def test_organization_role(domain):
    """ Organization own role """
    org_id = FIXTURE_ORGANIZATION_ID
    payload = dict(name="org-role-1", description="org-role-1", key="org-role-1")
    resp = await command_handler(domain, "create-org-role", payload, "organization", org_id)
    role = await domain.statemgr.fetch('organization-role', resp[0]["role_id"])
    
    update_payload = dict(role_id=role._id, updates=payload | {"name":"org-role-updated"})
    await command_handler(domain, "update-org-role", update_payload, "organization", org_id)
    await command_handler(domain, "remove-org-role", dict(role_id=role._id), "organization", org_id)
    
    item = await domain.statemgr.find_one('organization-role', identifier=role._id)
    assert item is None

# ------------------------------
# User Invitation Flow
# ------------------------------
@mark.asyncio
@mark.order(4)
async def test_invitation_context():
    pass
    """Invite a user by email with selected roles"""
    """Generate unique invitation code with expiration time"""
    """Prevent duplicate active invitations to same email/org"""
    """Revoke an unaccepted invitation"""
    """Accept invitation and convert to active profile"""


# ------------------------------
# Profile Management
# ------------------------------
@mark.asyncio
@mark.order(9)
async def test_profile_context():
    pass
    """Accepting invitation creates profile linked to organization"""
    """Assign multiple roles to a profile"""
    """Remove or revoke role from profile"""
    """Transition profile status to ACTIVE, LOCKED, INACTIVE"""
    """Prevent actions from LOCKED or INACTIVE profile"""

@mark.asyncio
@mark.order(9)
async def test_profile_role_context(domain):
    """ Test full lifecycle of profile-role: assign, duplicate, multiple, revoke, clear """
    PROFILE_ID = FIXTURE_PROFILE_ID
    ROLE_ID = "8094a542-cfea-4511-9fe2-9d57ff613189"
    base_payload = dict(role_id=ROLE_ID)

    # 0. Clear all role
    await command_handler(domain, "clear-role-from-profile", {}, "profile", PROFILE_ID)
    remaining = await domain.statemgr.find_all("profile-role", where=dict(profile_id=PROFILE_ID, _deleted=None))
    assert len(remaining) == 0
    # 1. Assign role
    role = await command_handler(domain, "assign-role-to-profile", base_payload, "profile", PROFILE_ID)
    assert len(role) == 1
    # 2. Assign duplicate role (should not duplicate)
    with pytest.raises(ValueError):
        await command_handler(domain, "assign-role-to-profile", base_payload, "profile", PROFILE_ID)
    # 4. Revoke one role
    revoke_payload = dict(profile_role_id=role[0]["_id"])
    await command_handler(domain, "revoke-role-from-profile", revoke_payload, "profile", PROFILE_ID)
    assert (await domain.statemgr.find_one('profile-role', identifier=role[0]["_id"])) is None
    # 3. Assign multiple roles
    system_roles = await domain.statemgr.find_all("ref--system-role")
    for _role in system_roles:
        await command_handler(domain, "assign-role-to-profile", dict(role_id=_role._id), "profile", PROFILE_ID)
    assert len(await domain.statemgr.find_all("profile-role", where={"profile_id": PROFILE_ID})) == len(system_roles)

    # # 5. Revoke non-existent role
    # # 6. Clear all roles
    # # 7. Clear roles for invalid profile

# ------------------------------
# Group Context and Profile Group
# ------------------------------
@mark.asyncio
@mark.order(14)
async def test_group_context():
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
