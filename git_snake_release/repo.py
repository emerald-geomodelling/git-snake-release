import subprocess
import os.path
import re
import string
import random
import toposort
from . import setuppy
from . import pyprojecttoml


def run_git(args, cwd=None, capture_output=True):
    """Run a git command and return the output."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
        check=True
    )
    return result.stdout.strip() if capture_output else None


def get_urls(path):
    output = run_git(["remote", "-v"], cwd=path)
    lines = output.split("\n") if output else []
    result = {}
    for line in lines:
        parts = re.split(r"[\t ]", line)
        if len(parts) >= 3 and parts[2] == "(fetch)":
            result[parts[0]] = parts[1]
    return result


def as_dependency(path):
    path = os.path.abspath(path)
    return {"name": os.path.split(path)[1], "url": get_urls(path)["origin"], "version": None}


def default_branch(path, candidates=None):
    """Resolve a repository's default branch.

    Resolution order:
      1. If ``candidates`` is given, the first name that exists as an
         ``origin/<name>`` remote-tracking branch. This lets a caller force a
         specific branch, or pass a safe ordered hint such as
         ``("main", "master")`` that adapts per repo.
      2. The ``origin/HEAD`` symbolic ref (set by ``git clone``) -- handles an
         arbitrary default branch name with no configuration.
      3. The ``HEAD branch`` reported by ``git remote show origin`` (network).
      4. ``"master"`` as a last-ditch fallback (the previously hard-coded value).
    """
    if candidates:
        for name in candidates:
            try:
                run_git(["rev-parse", "--verify", "--quiet",
                         f"refs/remotes/origin/{name}"], cwd=path)
                return name
            except subprocess.CalledProcessError:
                continue
    try:
        ref = run_git(["symbolic-ref", "refs/remotes/origin/HEAD"], cwd=path)
        if ref:
            return ref.rsplit("/", 1)[-1]
    except subprocess.CalledProcessError:
        pass
    try:
        out = run_git(["remote", "show", "origin"], cwd=path)
        match = re.search(r"HEAD branch:\s*(\S+)", out or "")
        if match:
            return match.group(1)
    except subprocess.CalledProcessError:
        pass
    return "master"


def checkout(path, url, version, default_branches=None, **kw):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        basepath, name = os.path.split(os.path.abspath(path))
        run_git(["clone", url.replace("git+http", "http"), name], cwd=basepath, capture_output=False)
        return default_branch(path, default_branches)
    branch = default_branch(path, default_branches)
    run_git(["checkout", branch], cwd=path, capture_output=False)
    run_git(["pull", "origin", branch], cwd=path, capture_output=False)
    return branch


def get_dependency_tree(path, default_branches=None):
    path = os.path.abspath(path)

    explored_dependencies = {}
    new_dependencies = []

    dep = as_dependency(path)
    new_dependencies.append(dep)

    basepath = os.path.split(path)[0]
    while new_dependencies:
        dep = new_dependencies.pop()

        if dep["name"] in explored_dependencies:
            continue
        explored_dependencies[dep["name"]] = dep

        checkout(os.path.join(basepath, dep["name"]), default_branches=default_branches, **dep)

        dep_path = os.path.join(basepath, dep["name"])
        # Try pyproject.toml first, fall back to setup.py
        if pyprojecttoml.has_pyproject_toml(dep_path):
            new = pyprojecttoml.get_dependencies(dep_path)
        else:
            new = setuppy.get_dependencies(dep_path)
        dep["dependencies"] = [item["name"] for item in new]
        new_dependencies.extend(new)

    return explored_dependencies


def random_name(prefix='temp-', length=10):
    return prefix + ''.join(random.choice(string.ascii_letters) for i in range(length))


def tag_exists(path, tag):
    """Check if a git tag already exists on the remote.

    Checks origin, not the local clone: a tag created by an earlier run but never
    pushed (e.g. the push failed) must NOT be treated as an existing release and
    skipped -- otherwise the run reports success while the remote stays untagged.
    --skip-existing means "already released", i.e. present on origin.
    """
    try:
        out = run_git(["ls-remote", "--tags", "origin", tag], cwd=path)
        return bool(out and out.strip())
    except subprocess.CalledProcessError:
        return False


def tag_release(path, url, version, all_dependencies, prefix, dry_run=False, skip_existing=False, default_branches=None, **kw):
    path = os.path.abspath(path)

    if dry_run:
        # In dry-run mode, just print what would happen
        return

    branch = checkout(path, url, version, default_branches=default_branches)

    # Check if tag already exists
    if skip_existing and tag_exists(path, version):
        print(f"  Tag '{version}' already exists, skipping...")
        return

    tmp = random_name()
    run_git(["checkout", "-b", tmp], cwd=path, capture_output=False)

    # Use pyproject.toml if available, otherwise setup.py
    if pyprojecttoml.has_pyproject_toml(path):
        pyprojecttoml.set_dependency_versions(path, all_dependencies)
        pyprojecttoml.set_version(path, version[len(prefix):])
        run_git(["add", "pyproject.toml"], cwd=path, capture_output=False)
    else:
        setuppy.set_dependency_versions(path, all_dependencies)
        setuppy.set_version(path, version[len(prefix):])
        run_git(["add", "setup.py"], cwd=path, capture_output=False)

    run_git(["commit", "--allow-empty", "-m", "Updated versions of dependencies"], cwd=path, capture_output=False)
    # -f so a stale local tag left by an earlier failed run is overwritten rather
    # than aborting here; tag_exists() already confirmed origin does not have it.
    run_git(["tag", "-f", version], cwd=path, capture_output=False)
    run_git(["checkout", branch], cwd=path, capture_output=False)
    run_git(["branch", "-D", tmp], cwd=path, capture_output=False)
    run_git(["push", "--tags", "origin", branch], cwd=path, capture_output=False)


def tag_releases(path, prefix, version, dry_run=False, skip_existing=False, default_branches=None):
    path = os.path.abspath(path)

    dependencies = get_dependency_tree(path, default_branches=default_branches)
    for dependency in dependencies.values():
        dependency["version"] = prefix + version

    basepath = os.path.split(path)[0]
    sorted_repos = toposort.toposort_flatten({key:value["dependencies"] for key, value in dependencies.items()}, sort=True)

    if dry_run:
        print()
        print("=" * 70)
        print("DRY RUN - No changes will be made")
        print("=" * 70)
        print()
        print(f"Tag to be created: {prefix}{version}")
        print(f"Total repositories: {len(sorted_repos)}")
        if skip_existing:
            print("(--skip-existing enabled: repos with existing tags will be skipped)")
        print()
        print("Repositories (in dependency order):")
        print("-" * 70)
        for i, repo_name in enumerate(sorted_repos, 1):
            dependency = dependencies[repo_name]
            dep_path = os.path.join(basepath, dependency["name"])
            config_file = "pyproject.toml" if pyprojecttoml.has_pyproject_toml(dep_path) else "setup.py"
            dep_count = len(dependency.get("dependencies", []))
            already_tagged = tag_exists(dep_path, prefix + version) if skip_existing else False
            status = " [EXISTS - will skip]" if already_tagged else ""
            print(f"  {i:2}. {repo_name}{status}")
            print(f"      URL: {dependency['url']}")
            print(f"      Tag: {prefix}{version}")
            print(f"      Config: {config_file}")
            print(f"      Dependencies: {dep_count}")
            print()
        print("-" * 70)
        print(f"Total: {len(sorted_repos)} repositories would be tagged with {prefix}{version}")
        return

    for repo_name in sorted_repos:
        print()
        print("Making release for", repo_name)
        print("================================================================")
        dependency = dependencies[repo_name]
        tag_release(os.path.join(basepath, dependency["name"]), all_dependencies=dependencies, prefix=prefix, dry_run=dry_run, skip_existing=skip_existing, default_branches=default_branches, **dependency)
