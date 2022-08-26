import re
import os

def get_dependencies(path):
    with open(os.path.join(path, "setup.py")) as f:
        code = f.read()
    return [
        re.match('[\'"](?P<name>[^ ]*) +@ +(?P<url>git\+https://[^/]*/[^@ \'"]*)(@(?P<version>[^ ]*))?[\'"]', dep).groupdict()
        for dep in re.findall('[\'"][^\'"]*git\+https://[^\'"]*[\'"]', code)]
    
def merge_dependency_version(code, name, version, **kw):
    return re.sub(
        '[\'"](?P<name>%s) +@ +(?P<url>git\+https://[^/]*/[^@ \'"]*)(@(?P<version>[^ ]*))?[\'"]' % (name,),
        '"\g<name> @ \g<url>@%s"' % (version,), code)

def merge_dependency_versions(code, dependencies):
    for name, dependency in dependencies.items():
        code = merge_dependency_version(code, **dependency)
    return code

def set_dependency_versions(path, dependencies):
    filepath = os.path.join(path, "setup.py")
    with open(filepath) as f:
        code = f.read()
    code = merge_dependency_versions(code, dependencies)
    with open(filepath, "w") as f:
        f.write(code)

def get_version(path):
    with open(os.path.join(path, "setup.py")) as f:
        code = f.read()
    return re.search('version *= *["\'](?P<version>.*)["\']', code).groupdict()["version"]

def merge_version(code, version):
    return re.sub('(?P<head>version *= *)["\'](?P<version>.*)["\']', '\g<head>"%s"' % version, code)

def set_version(path, version):
    filepath = os.path.join(path, "setup.py")
    with open(filepath) as f:
        code = f.read()
    code = merge_version(code, version)
    with open(filepath, "w") as f:
        f.write(code)
