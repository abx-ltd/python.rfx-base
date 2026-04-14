#!/usr/bin/env python3
"""
Bump [project].version in pyproject.toml (semver M.m.p), commit, tag releases/gh/<version>,
push, create GitHub Release. Uses git and gh CLI. Repository root = two levels above this file.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
TAG_PREFIX = "releases/gh/"


def _die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd or ROOT, check=True)


def read_version() -> str:
    with PYPROJECT.open("rb") as f:
        data = tomllib.load(f)
    v = data.get("project", {}).get("version")
    if not v:
        _die("pyproject.toml [project] has no version")
    return str(v).strip()


def write_version(old: str, new_ver: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    for q in ('"', "'"):
        needle = f"version = {q}{old}{q}"
        if needle in text:
            text_new = text.replace(needle, f'version = "{new_ver}"', 1)
            PYPROJECT.write_text(text_new, encoding="utf-8")
            return
    _die("could not find exact [project] version line in pyproject.toml")


def bump_semver(version: str, kind: str) -> str:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version.strip())
    if not m:
        _die(
            f"version must be M.m.p for automated bump (no pre-release suffix), got {version!r}"
        )
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if kind == "patch":
        patch += 1
    elif kind == "minor":
        minor += 1
        patch = 0
    elif kind == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        _die(f"invalid bump kind: {kind!r}")
    return f"{major}.{minor}.{patch}"


def cmd_print() -> None:
    v = read_version()
    print(f"Current version: {v}")
    print("Usage: just release patch | minor | major")
    print(
        "  Bumps pyproject.toml [project].version, commits, tags "
        f"{TAG_PREFIX}<version>, pushes, creates a GitHub Release (gh)."
    )


def require_gh() -> None:
    if not shutil.which("gh"):
        _die(
            "GitHub CLI (gh) is required. Install: https://cli.github.com",
            code=2,
        )


def cmd_release(kind: str) -> None:
    require_gh()
    old = read_version()
    new_ver = bump_semver(old, kind)
    write_version(old, new_ver)

    _run(["git", "add", "pyproject.toml"])
    _run(["git", "commit", "-m", f"Bump version to {new_ver}"])
    tag = f"{TAG_PREFIX}{new_ver}"
    _run(["git", "tag", "-a", tag, "-m", f"Release v{new_ver}"])
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not branch:
        _die("detached HEAD: checkout a branch before releasing", code=3)
    _run(["git", "push", "origin", branch])
    _run(["git", "push", "origin", tag])
    _run(
        [
            "gh",
            "release",
            "create",
            tag,
            "--title",
            f"v{new_ver}",
            "--generate-notes",
        ]
    )
    print(f"Released {new_ver} ({tag})")


def main() -> None:
    kind = (sys.argv[1] if len(sys.argv) > 1 else "print").strip().lower()
    if kind in ("print", "help", "-h", "--help"):
        cmd_print()
        return
    if kind in ("patch", "minor", "major"):
        cmd_release(kind)
        return
    _die(f"unknown command: {kind!r} (use print, patch, minor, or major)")


if __name__ == "__main__":
    main()
