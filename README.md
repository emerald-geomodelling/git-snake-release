# git-snake-release

The problem: You have broken up your codebase in sensible small repositories, one python library on each.
You have made a new release of one of them, but now you need to update all that depends on it, and on that in turn etc,
and make them all depend on this new specific version.

The solution:

```
git-snake-release --prefix 2024-11-27-v. --version 0.17.2 path/to/mygitrepo
```

This will recursively find all git based dependencies (`name @ git+https://url/to/repo.git`), tag them all with the same tag,
and update **pyproject.toml** (or setup.py for legacy projects) in each of them to link to the new versions of dependencies.

## Supported project formats

- **pyproject.toml** (preferred, PEP 621) - Dependencies in `[project].dependencies`
- **setup.py** (legacy) - Dependencies in `install_requires`

## Installation

```bash
pip install git+https://github.com/emerald-geomodelling/git-snake-release.git
```

## Dry Run

Preview what would be done without making any changes:

```bash
git-snake-release --dry-run --prefix "2024-11-27-v." --version 0.17.2 /path/to/release-all
```

This shows all repositories in dependency order with their URLs, tags, and config file types.

## Example

```bash
# Tag all repos with today's date and version 0.17.2
git-snake-release --prefix "2024-11-27-v." --version 0.17.2 /path/to/release-all
```

This will:
1. Recursively discover all git-based dependencies
2. Build a dependency tree using topological sort
3. For each repository (in dependency order):
   - Checkout master and pull latest
   - Update dependency versions in pyproject.toml/setup.py
   - Commit the changes
   - Create a git tag
   - Push tags to origin
