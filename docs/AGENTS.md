# Documentation conventions for agents

Instructions for maintaining files under `./docs/` unless a subdirectory specifies otherwise.

## `docs/changelog/`

- **Append-only audit trail.** Add a new record file for each material change to the specification.
- **Do not rewrite or delete past records.** Correct errors by appending a follow-up record if needed.

## `docs/release/`

- Holds **release notes** and **unreleased** change tracking.
- Content is **managed by the `flctl release` command**, except **`UNRELEASED.md`**, which is maintained manually (or by agreed process outside `flctl`).

## Filenames under `./docs/`

For files inside each directory under `./docs/`, unless that directory’s own rules say otherwise:

- Use **dots** between the leading numeric prefix and the rest of the name.
- Prefix with **two digits**, then `.`, then the slug, e.g. `01.overview.md`, `02.example-domain.md`, `01.project-scope.md`.
- **Multi-word slugs** use **hyphens** inside the **last** segment, e.g. `02.platform-description.md`.
- Use **singular nouns** in the filename slug only. Headings and prose inside the file may use natural plural titles (e.g. file `03.api-specification.md` with title “API specifications”).
