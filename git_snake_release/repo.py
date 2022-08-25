import pieshell
from pieshell import env
import os.path
import re
import string
import random
import toposort
from . import setuppy

def get_urls(path):
    _ = env()
    +_.cd(path)
    return dict([item[:2] for item in [re.split(r"[\t ]", item) for item in _.git.remote("-v")] if item[2] == "(fetch)"])
 
def as_dependency(basepath, name):
    path = os.path.join(basepath, name)
    return {"name": name, "url": get_urls(path)["origin"], "version": None}

def checkout(basepath, name, url, version, **kw):
    _ = env()
    
    +_.cd(basepath)

    path = os.path.join(basepath, name)
    if not os.path.exists(path):
        +_.git.clone(url.replace("git+http", "http"), name)
    else:
        +_.cd(name)
        +_.git.checkout("master")
        +_.git.pull("origin", "master")


def get_dependency_tree(basepath, name):
    explored_dependencies = {}
    new_dependencies = []
    
    path = os.path.join(basepath, name)
    dep = as_dependency(basepath, name)
    new_dependencies.append(dep)

    while new_dependencies:
        dep = new_dependencies.pop()

        if dep["name"] in explored_dependencies:
            continue
        explored_dependencies[dep["name"]] = dep
        
        checkout(basepath, **dep)

        new = setuppy.get_dependencies(os.path.join(basepath, dep["name"]))
        dep["dependencies"] = [item["name"] for item in new]
        new_dependencies.extend(new)

    return explored_dependencies

def random_name(prefix='temp-', length=10):
    return prefix + ''.join(random.choice(string.ascii_letters) for i in range(length))

def tag_release(basepath, name, url, version, all_dependencies, prefix, **kw):
    repopath = os.path.join(basepath, name)
    checkout(basepath, name, url, version)
    _ = env()
    +_.cd(os.path.join(basepath, name))
    tmp = random_name()
    +_.git.checkout("-b", tmp)
    setuppy.set_dependency_versions(repopath, all_dependencies)
    setuppy.set_version(repopath, version[len(prefix):])
    +_.git.add("setup.py")
    +_.git.commit("--allow-empty", "-m", "Updated versions of dependencies")
    +_.git.tag(version)
    +_.git.checkout("master")
    +_.git.branch("-D", tmp)
    +_.git.push("--tags", "origin", "master")

def tag_releases(basepath, name, prefix, version):
    dependencies = get_dependency_tree(basepath, name)
    for dependency in dependencies.values():
        dependency["version"] = prefix + version
        
    for repo in toposort.toposort_flatten({key:value["dependencies"] for key, value in dependencies.items()}, sort=True):
        print()
        print("Making release for", repo)
        print("================================================================")
        tag_release(basepath, all_dependencies=dependencies, prefix=prefix, **dependencies[repo])

