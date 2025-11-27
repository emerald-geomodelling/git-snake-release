"""
Module for parsing and modifying pyproject.toml files.
Handles git-based dependencies in the format:
    "package-name @ git+https://user:token@github.com/org/repo.git[@version]"
"""
import re
import os
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python
import tomli_w


def get_dependencies(path):
    """
    Extract git-based dependencies from pyproject.toml.

    Returns list of dicts with keys: name, url, version (or None)
    """
    filepath = os.path.join(path, "pyproject.toml")
    if not os.path.exists(filepath):
        return []

    with open(filepath, "rb") as f:
        data = tomllib.load(f)

    dependencies = data.get("project", {}).get("dependencies", [])

    git_deps = []
    for dep in dependencies:
        # Match: "name @ git+https://[user:token@]host/org/repo.git[@version]"
        # The URL may contain credentials like user:token@ before the host
        match = re.match(
            r'(?P<name>[^\s@]+)\s*@\s*(?P<url>git\+https://[^\s]+\.git)(?:@(?P<version>[^\s]+))?$',
            dep.strip()
        )
        if match:
            git_deps.append(match.groupdict())

    return git_deps


def merge_dependency_version(dep_string, name, version, **kw):
    """
    Update a single dependency string with a new version tag.
    """
    # Pattern to match the dependency and optionally existing version
    # The URL may contain credentials, so match up to .git
    pattern = rf'({re.escape(name)})\s*@\s*(git\+https://[^\s]+\.git)(?:@[^\s]+)?$'
    replacement = rf'\1 @ \2@{version}'
    return re.sub(pattern, replacement, dep_string)


def set_dependency_versions(path, dependencies):
    """
    Update all git dependencies in pyproject.toml with new versions.

    Args:
        path: Path to directory containing pyproject.toml
        dependencies: Dict mapping package names to dependency info (with 'version' key)
    """
    filepath = os.path.join(path, "pyproject.toml")

    with open(filepath, "rb") as f:
        data = tomllib.load(f)

    if "project" not in data or "dependencies" not in data["project"]:
        return

    new_deps = []
    for dep in data["project"]["dependencies"]:
        # Check if this is a git dependency that needs updating
        updated = False
        for name, dep_info in dependencies.items():
            if dep.strip().startswith(f"{name} @") or dep.strip().startswith(f"{name}@"):
                if dep_info.get("version"):
                    dep = merge_dependency_version(dep, name, dep_info["version"])
                    updated = True
                    break
        new_deps.append(dep)

    data["project"]["dependencies"] = new_deps

    with open(filepath, "wb") as f:
        tomli_w.dump(data, f)


def get_version(path):
    """
    Get the project version from pyproject.toml.
    """
    filepath = os.path.join(path, "pyproject.toml")

    with open(filepath, "rb") as f:
        data = tomllib.load(f)

    return data.get("project", {}).get("version", "0.0.0")


def set_version(path, version):
    """
    Set the project version in pyproject.toml.
    """
    filepath = os.path.join(path, "pyproject.toml")

    with open(filepath, "rb") as f:
        data = tomllib.load(f)

    if "project" not in data:
        data["project"] = {}

    data["project"]["version"] = version

    with open(filepath, "wb") as f:
        tomli_w.dump(data, f)


def has_pyproject_toml(path):
    """
    Check if a directory contains a pyproject.toml file.
    """
    return os.path.exists(os.path.join(path, "pyproject.toml"))
