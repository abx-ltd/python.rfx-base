
# Bump pyproject.toml version (Python), tag `releases/gh/<version>`, push, `gh release create`.
@release RELEASE_TYPE="print":
    python3 "{{ justfile_directory() }}/.command/pycmd/release.py" {{ RELEASE_TYPE }}
