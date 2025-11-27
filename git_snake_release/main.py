from . import repo
import click
import os.path

@click.command()
@click.option('--prefix', default="release-", help='Prefix for git tags (not used for version= in setup.py). Default: release-')
@click.option('--version', help='Version to tag')
@click.option('--dry-run', is_flag=True, default=False, help='Print what would be done without making any changes')
@click.argument('path', type=str)
def main(path, prefix, version, dry_run, **kw):
    """Tag a repository and all dependencies with a version (git tag)"""
    try:
        repo.tag_releases(path, prefix, version, dry_run=dry_run)
    except Exception as e:
        print(e)
        import pdb, sys
        sys.last_traceback = sys.exc_info()[2]
        pdb.pm()

if __name__ == '__main__':
    main()
