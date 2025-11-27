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

def tag_release(path, url, version, all_dependencies, prefix, **kw):
    path = os.path.abspath(path)
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

def tag_releases(path, prefix, version):
    path = os.path.abspath(path)
    
    dependencies = get_dependency_tree(path)
    for dependency in dependencies.values():
        dependency["version"] = prefix + version

    basepath = os.path.split(path)[0]
    for repo in toposort.toposort_flatten({key:value["dependencies"] for key, value in dependencies.items()}, sort=True):
        print()
        print("Making release for", repo)
        print("================================================================")
        dependency = dependencies[repo]
        tag_release(os.path.join(basepath, dependency["name"]), all_dependencies=dependencies, prefix=prefix, **dependency)

