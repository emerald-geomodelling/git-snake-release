import pieshell
from pieshell import env
import os.path
import re
from . import deps

def get_urls(path):
    _ = env()
    _.cd(path).run_interactive()
    return dict([item[:2] for item in [re.split(r"[\t ]", item) for item in _.git.remote("-v")] if item[2] == "(fetch)"])
 
def as_dependency(basepath, name):
    path = os.path.join(basepath, name)
    return {"name": name, "url": get_urls(path)["origin"], "version": None}

def checkout(basepath, name, url, version, **kw):
    _ = env()
    
    _.cd(basepath).run_interactive()

    path = os.path.join(basepath, name)
    if not os.path.exists(path):
        _.git.clone(url.replace("git+http", "http"), name).run_interactive()
    else:
        _.cd(name).run_interactive()
        _.git.checkout("master").run_interactive()
        _.git.pull("origin", "master").run_interactive()


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

        new = deps.get_dependencies(os.path.join(basepath, dep["name"]))
        dep["dependencies"] = [item["name"] for item in new]
        new_dependencies.extend(new)

    return explored_dependencies

def set_dependency_versions(basepath, repo, dependencies):
    set_dependency_versions(os.path.join(basepath, repo), dependencies)
    _ = env()
    _.cd(os.path.join(basepath, name))
    _.git.commit(message="Version bump")
    
def tag_release(basepath, name, url, version):
    checkout(basepath, name, url, version)
    _ = env()
    _.cd(os.path.join(basepath, name)).run_interactive()
    _.git.tag(version).run_interactive()
    _.git.push("--tags", "origin", "master").run_interactive()

def tag_releases(basepath, name, version):
    dependencies = git_snake_release.repo.get_dependency_tree(basepath, name)
    for dependency in dependencies:
        dependency["version"] = version
    
    for repo in toposort.toposort_flatten({key:value["dependencies"] for key, value in dependencies.items()}, sort=True):
        set_dependency_versions(os.path.join(basepath, repo), dependencies):
        tag_release(basepath, repo, ddependencies[repo]["url"], version)
