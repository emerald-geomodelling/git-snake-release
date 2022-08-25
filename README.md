# git-snake-release

The problem: You have broken up your codebase in sensible small repositories, one python library on each.
You have made a new release of one of them, but now you need to update all that depends on it, and on that in turn etc,
and make them all depend on this new specific version.

The solution:

```
git-snake-release --version some-tagname-1234 path/to/mygitrepo
```

This will recursively find all git based dependencies (`name @ git+https://url/to/repo.git`), tag them all with the same tag,
and update setup.py in each of them to link to the new versions of dependencies (`name @ git+https://url/to/repo.git@some-tagname-1234`).
