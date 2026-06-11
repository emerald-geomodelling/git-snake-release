# Changelog

## 2026-06-11

### Changed

- **Default branch no longer hard-coded to `master`.** `git-snake-release` now resolves each repository's default branch instead of assuming `master`, so repos whose default branch is `main` (or any other name) can be tagged. Resolution order: an optional caller-supplied candidate list, then `origin/HEAD`, then `git remote show origin`, falling back to `master`.

### Added

- **`--default-branch` option** (repeatable): supply candidate default branch name(s) in priority order. The first that exists in a given repo is used; if none match (or none are given) the branch is auto-detected. Example: `--default-branch main --default-branch master`.

### Motivation

The branch was hard-coded as `master` in `checkout`/`tag_release`, so any repo using `main` (e.g. forked external libraries added to the release graph) could not be tagged. Auto-detection handles arbitrary branch names with no configuration, while the option allows forcing or hinting a branch when needed.

## 2026-01-29

### Added

- **`--skip-existing` flag**: New CLI option that skips repositories where the target tag already exists instead of failing with a fatal error.

### Motivation

When releasing multiple projects that share common dependencies, running `git-snake-release` on each project would fail on shared dependencies that were already tagged by a previous release.

For example, if `project-a` and `project-b` both depend on `shared-library`, running:

```bash
git-snake-release --prefix "2026-01-29-v." --version 0.17.9 /path/to/project-a
git-snake-release --prefix "2026-01-29-v." --version 0.17.9 /path/to/project-b
```

The second command would fail with `fatal: tag '2026-01-29-v.0.17.9' already exists` when it tried to tag `shared-library`.

### Usage

```bash
# Skip repos that already have the tag
git-snake-release --prefix "2026-01-29-v." --version 0.17.9 --skip-existing /path/to/repo

# Preview which repos will be skipped (dry run)
git-snake-release --prefix "2026-01-29-v." --version 0.17.9 --skip-existing --dry-run /path/to/repo
```

In dry-run mode with `--skip-existing`, repos that already have the tag are marked with `[EXISTS - will skip]`.

### Files Changed

- `git_snake_release/repo.py`: Added `tag_exists()` helper function and `skip_existing` parameter to `tag_release()` and `tag_releases()` functions
- `git_snake_release/main.py`: Added `--skip-existing` CLI option
