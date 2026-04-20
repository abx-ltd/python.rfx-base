# Override in .env (see .env.example)
PKGINFO := env("PKGINFO", "src/app_main/pkginfo.py")

# Bump pyproject version, sync pkginfo, commit, tag, and push (e.g. `just release patch`)
# Run from the app root; `flctl` is provided via the `flctl` package (see pyproject).
[no-cd]
release RELEASE_TYPE="print" RELEASE_LABEL="none":
    uv run flctl release python -- {{ PKGINFO }} {{ RELEASE_TYPE }} {{ RELEASE_LABEL }}

# Same as release with --force (dirty working tree allowed)
[no-cd]
@release-force RELEASE_TYPE="print" RELEASE_LABEL="none":
    uv run flctl release python --force -- {{ PKGINFO }} {{ RELEASE_TYPE }} {{ RELEASE_LABEL }}
