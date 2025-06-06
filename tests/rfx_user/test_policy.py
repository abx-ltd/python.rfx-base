import pytest
import time
from fluvius.domain.context import DomainTransport
from rfx_user import UserProfileDomain, logger


FIXTURE_REALM = "rfx-user-testing"
FIXTURE_USER_ID = "88212396-02c5-46ae-a2ad-f3b7eb7579c0"
FIXTURE_ORGANIZATION_ID = "d36d4aac-e224-488a-a801-83fedcc2ab39"
FIXTURE_PROFILE_ID = "3a93d8ad-23ad-4457-85c8-9e6cfcb1d6f4"


@pytest.fixture
def domain():
	return UserProfileDomain(None)


@pytest.mark.asyncio
async def test_command_policy(domain):
	sub = FIXTURE_PROFILE_ID
	org = FIXTURE_ORGANIZATION_ID
	dom = "user-profile"
	act = None
	res = None
	rid = None

	testcases = [
		("create-organization", "organization", "", True),
		("update-organization", "organization", org, True),
		("deactivate-organization", "organization", org, True),
		("create-org-role", "organization", org, True),
		("update-org-role", "organization", org, True),
		("remove-org-role", "organization", org, True),
		("send-invitation", "invitation", "", True),
		("cancel-invitation", "invitation", sub, False),
		("update-profile", "profile", sub, True),
		("deactivate-profile", "profile", sub, True),
		("assign-role-to-profile", "profile", sub, True),
		("revoke-role-from-profile", "profile", sub, True),
		("clear-role-from-profile", "profile", sub, True),
		("add-group-to-profile", "profile", sub, True),
		("remove-group-from-profile", "profile", sub, True),
		("assign-group-to-profile", "profile", sub, True),
		("revoke-group-from-profile", "profile", sub, True),
		("clear-group-from-profile", "profile", sub, True),
		("send-action", "user", FIXTURE_USER_ID, False),
	]
	for act, res, rid, expect in testcases:
		prev = time.time()
		rs = await domain.policymgr.check(sub, org, dom, res, rid, act)
		logger.info("[%ss] Result %s" % (time.time() - prev, rs))
		assert rs.allowed == expect
