# Changelog

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
