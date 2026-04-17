# Override in .env (see .env.example)
PKGINFO := env("PKGINFO", "src/app_main/pkginfo.py")

# Bump pyproject version, sync pkginfo, commit, tag, and push (e.g. `just release patch`)
# Run from the app root; `fluvius_manager` must be on PATH / importable.
release RELEASE_TYPE="print" RELEASE_LABEL="none":
    python3 -m fluvius_manager release pkg -- {{ PKGINFO }} {{ RELEASE_TYPE }} {{ RELEASE_LABEL }}

# Same as release with --force (dirty working tree allowed)
@release-force RELEASE_TYPE="print" RELEASE_LABEL="none":
    python3 -m fluvius_manager release pkg --force -- {{ PKGINFO }} {{ RELEASE_TYPE }} {{ RELEASE_LABEL }}
