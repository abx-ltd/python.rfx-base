import casbin

def run():
    e = casbin.Enforcer("model.conf", "policy.csv")

    test_cases = [
        ("profile-2", "org-2", "project:123", "update"),  # ✅ match all
        ("profile-2", "org-2", "project:999", "update"),  # ❌ no g2
        ("profile-2", "org-2", "group:abc", "manage"),    # ✅
        ("profile-2", "org-2", "group:def", "manage"),    # ❌ no g2

        ("profile-3", "org-2", "project:124", "read"),    # ✅ reviewer with g2
        ("profile-3", "org-2", "project:123", "read"),    # ❌ no g2
        ("profile-3", "org-2", "project:124", "update"),  # ❌ not allowed action

        ("profile-1", "org-1", "project:124", "update"),  # ❌ not allowed action
    ]

    for profile, dom, res, act in test_cases:
        result = e.enforce(profile, dom, res, act)
        print(f"[{profile}] -> ({dom}, {res}, {act}) = {'✅ ALLOWED' if result else '❌ DENIED'}")

if __name__ == "__main__":
    run()
