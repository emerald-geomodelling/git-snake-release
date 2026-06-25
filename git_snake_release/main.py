from . import repo
import click
import os.path

@click.command()
@click.option('--prefix', default="release-", help='Prefix for git tags (not used for version= in setup.py). Default: release-')
@click.option('--version', help='Version to tag')
@click.option('--dry-run', is_flag=True, default=False, help='Print what would be done without making any changes')
@click.option('--skip-existing', is_flag=True, default=False, help='Skip repositories that already have the tag instead of failing')
@click.option('--default-branch', 'default_branches', multiple=True,
              help='Candidate default branch name(s), in priority order. The '
                   'first that exists in a given repo is used; if none match '
                   '(or none given) the default branch is auto-detected from '
                   'origin/HEAD. Repeatable, e.g. --default-branch main '
                   '--default-branch master.')
@click.argument('path', type=str)
def main(path, prefix, version, dry_run, skip_existing, default_branches, **kw):
    """Tag a repository and all dependencies with a version (git tag)"""
    repo.tag_releases(path, prefix, version, dry_run=dry_run, skip_existing=skip_existing,
                      default_branches=default_branches or None)

if __name__ == '__main__':
    main()
