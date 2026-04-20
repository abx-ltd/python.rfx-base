# Fluvius changelog

Use this file as the **guide for maintaining** changelog entries under `docs/changelog/`.

This folder holds the **library changelog** for Fluvius: release notes and, when needed, **migration guidance** for consumers (applications, internal packages, and operators).

## When to update

Update the changelog in these situations:

1. **User request** — When someone asks for a changelog entry for work that was merged or is about to merge, add or adjust the entry as part of that task.
2. **Commit / merge request** — When your change is **user-visible** or **integration-affecting** (API surface, behavior, defaults, config, CLI, database expectations, or documented contracts), add an entry in the same MR or commit series as the code change.
   Trivial changes (typos in comments, internal refactors with no behavior change) do not need an entry unless they are part of a larger release note.

If you are unsure, prefer a short entry; duplicates can be edited before release.

## How entries are tracked

Changelog entries use **filenames**, not package version, as the primary organizer. Each file follows:

**`NNN.YYYY-MM-DD.<title>.md`**

- **`NNN`** — Three-digit serial number (`001`, `002`, ...), zero-padded. Use the **next** serial not already used in `docs/changelog/` so files sort predictably and stay unique.
- **`YYYY-MM-DD`** — ISO 8601 **calendar date** for **when this changelog file is added** (the day the log entry is written and committed). Use that date in the filename and in the optional *Recorded ...* line. Do **not** set it from the last commit date of the code being described unless you are writing the log on that same day.
- **`<title>`** — Short **slug** for the topic: lowercase, words separated by **hyphens** (for example, `query-auth-and-fluvius-query-tests`). This becomes the human-facing title in the file (see below).

Examples:

- `001.2026-04-08.query-auth-and-fluvius-query-tests.md`

If you add **several changelog files on the same calendar day**, use **separate files** with the same date but different serials and titles (or one file if you prefer a single combined note—team choice; the filename pattern still applies).

Inside each file, use a level-1 heading with a **readable title** derived from the slug, then on the following lines (same **`YYYY-MM-DD`** as in the filename; **Last release** from **`pyproject.toml`** at commit time):

```markdown
*Recorded: YYYY-MM-DD.*

*Last release: <current version number>.*
```

Package version in **`pyproject.toml`** may still be mentioned in the body when it helps readers.

Example entry: [001.2026-04-08.query-auth-and-fluvius-query-tests.md](./001.2026-04-08.query-auth-and-fluvius-query-tests.md).

## Release notes file (`docs/release/UNRELEASED.md`)

For **every** new changelog file you add under `docs/changelog/`, also add a **short summary** (one line or a bullet) into **`docs/release/UNRELEASED.md`**. That file is the rolling draft of what will ship as the **GitHub Release** notes for the next version.

When you run **`flctl release python`**, the tool renames `UNRELEASED.md` to **`docs/release/RELEASE-<version>.md`**, uses it as the release body for **`gh release create`**, and writes a fresh **`UNRELEASED.md`** for the next development cycle. Keep the detailed narrative in `docs/changelog/`; keep `UNRELEASED.md` as a concise, user-facing summary for the release page.

## Entry format

Use a consistent structure so readers can scan quickly and find migrations.

### Sections (recommended)

Use headings inspired by [Keep a Changelog](https://keepachangelog.com/):

- **Added** — New features or APIs.
- **Changed** — Behavior or API changes that remain backward compatible.
- **Deprecated** — Features marked for removal; point to replacements.
- **Removed** — Breaking removals.
- **Fixed** — Bug fixes.
- **Security** — Security-relevant fixes.

Order sections as above when more than one applies.

### Migration instructions

For any change that **requires action** from consumers (breaking API, config rename, removal of a flag, database schema change, CLI change, and so on), add a **Migration** subsection under the relevant section or entry.

**Migration blocks should include:**

- **Who is affected** — for example, "FastAPI apps using `configure_query_manager`", "callers of `QueryManager.query_resource`".
- **What changed** — One or two sentences.
- **What to do** — Numbered steps, SQL snippets, or code before/after. Link to docs or issues when useful.

Example:

```markdown
### Changed

- **Query HTTP routes** now require a resolved `AuthorizationContext` on `request.state`. Unauthenticated requests receive `403` with code `Q00.003`.

#### Migration

- **Affected:** Applications exposing Fluvius query routes without `@auth_required` / `get_auth_context`.
- **Action:**
  1. Ensure query routes run after authentication middleware so `request.state.auth_context` is set.
  2. Remove any reliance on implicit anonymous query access; tests should pass an explicit `AuthorizationContext` (see `tests/fluvius_query/conftest.py`).
```

For database or operational steps, keep commands copy-pasteable and name the schema or connector (for example, `python -m fluvius_manager database create-schema ...`).

## Style

- Write in **complete sentences**; use present tense for what the entry *does* ("Adds", "Removes").
- Reference PRs or issue IDs when helpful.
- Prefer one logical change per bullet; split large bullets.

## Review

Before tagging a release, skim recent changelog files for missing **Migration** blocks next to any **Removed** or breaking **Changed** items.
