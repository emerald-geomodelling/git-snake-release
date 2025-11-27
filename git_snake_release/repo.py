import pieshell
from pieshell import env
import os.path
import re
import string
import random
import toposort
from . import setuppy
from . import pyprojecttoml

def get_urls(path):
    _ = env()
    +_.cd(path)
    return dict([item[:2] for item in [re.split(r"[\t ]", item) for item in _.git.remote("-v")] if item[2] == "(fetch)"])
 
def as_dependency(path):
    path = os.path.abspath(path)
    return {"name": os.path.split(path)[1], "url": get_urls(path)["origin"], "version": None}

def checkout(path, url, version, **kw):
    path = os.path.abspath(path)
    _ = env()
    if not os.path.exists(path):
        basepath, name = os.path.split(os.path.abspath(path))
        +_.cd(basepath)
        +_.git.clone(url.replace("git+http", "http"), name)
    else:
        +_.cd(path)
        +_.git.checkout("master")
        +_.git.pull("origin", "master")


def get_dependency_tree(path):
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
        
        checkout(os.path.join(basepath, dep["name"]), **dep)

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

def tag_release(path, url, version, all_dependencies, prefix, dry_run=False, **kw):
    path = os.path.abspath(path)

    if dry_run:
        # In dry-run mode, just print what would happen
        return

    checkout(path, url, version)
    _ = env()
    +_.cd(path)
    tmp = random_name()
    +_.git.checkout("-b", tmp)

    # Use pyproject.toml if available, otherwise setup.py
    if pyprojecttoml.has_pyproject_toml(path):
        pyprojecttoml.set_dependency_versions(path, all_dependencies)
        pyprojecttoml.set_version(path, version[len(prefix):])
        +_.git.add("pyproject.toml")
    else:
        setuppy.set_dependency_versions(path, all_dependencies)
        setuppy.set_version(path, version[len(prefix):])
        +_.git.add("setup.py")

    +_.git.commit("--allow-empty", "-m", "Updated versions of dependencies")
    +_.git.tag(version)
    +_.git.checkout("master")
    +_.git.branch("-D", tmp)
    +_.git.push("--tags", "origin", "master")

def tag_releases(path, prefix, version, dry_run=False):
    path = os.path.abspath(path)

    dependencies = get_dependency_tree(path)
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
        print()
        print("Repositories (in dependency order):")
        print("-" * 70)
        for i, repo_name in enumerate(sorted_repos, 1):
            dependency = dependencies[repo_name]
            dep_path = os.path.join(basepath, dependency["name"])
            config_file = "pyproject.toml" if pyprojecttoml.has_pyproject_toml(dep_path) else "setup.py"
            dep_count = len(dependency.get("dependencies", []))
            print(f"  {i:2}. {repo_name}")
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
        tag_release(os.path.join(basepath, dependency["name"]), all_dependencies=dependencies, prefix=prefix, dry_run=dry_run, **dependency)

