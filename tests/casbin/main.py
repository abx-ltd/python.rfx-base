import casbin
from pathlib import Path

def main():
    # Load model and policy files
    model_path = Path("model.conf").resolve()
    policy_path = Path("policy.csv").resolve()
    enforcer = casbin.Enforcer(str(model_path), str(policy_path))

    # List of test cases
    test_cases = [
        # (profile, org, domain, resource, resource_id, action, expected_result, description)
        ("profile-123", "org-1", "domain-1", "project", "",       "create", True,  "project-admin creating project (no resource_id)"),
        ("profile-123", "org-1", "domain-1", "project", "proj-1", "update", True,  "project-admin updating granted project"),
        ("profile-456", "org-1", "domain-1", "project", "proj-2", "view",   True,  "team-lead viewing granted project"),
        ("profile-456", "org-1", "domain-1", "project", "proj-1", "update", False, "team-lead lacks update permission"),
        ("profile-456", "org-1", "domain-1", "project", "",       "create", False, "team-lead not allowed to create"),
        ("profile-123", "org-1", "domain-1", "project", "proj-X", "update", False, "resource not granted via g2"),
        ("profile-123", "org-2", "domain-1", "project", "",       "create", False, "wrong organization for role"),
        ("profile-999", "org-1", "domain-1", "project", "proj-1", "view",   False, "unknown profile"),
        ("profile-123", "org-1", "domain-1", "project", "proj-2", "view",   True,  "project-admin has view via update policy"),
        ("profile-123", "org-1", "domain-2", "project", "proj-1", "update", False, "wrong domain"),
        ("profile-123", "org-1", "domain-1", "project", "proj-2", "delete", False, "no delete policy defined"),
    ]

    print("🔐 Casbin Extended Test Results\n" + "-" * 70)
    for i, (profile, org, domain, resource, res_id, action, expected, desc) in enumerate(test_cases, 1):
        result, explain = enforcer.enforce_ex(profile, org, domain, resource, res_id, action)
        print(explain)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{i:02d}) {status} | {desc:<45} → result: {result} | expected: {expected}")

if __name__ == "__main__":
    main()
