from . import repo
import click
import os.path

@click.command()
@click.option('--version', help='Version to tag')
@click.argument('path', type=str)
def main(path, version, **kw):
    """Tag a repository and all dependencies with a version (git tag)"""
    basepath, name = os.path.split(os.path.abspath(path))
    try:
        repo.tag_releases(basepath, name, version)
    except Exception as e:
        print(e)
        import pdb, sys
        sys.last_traceback = sys.exc_info()[2]
        pdb.pm()
    
if __name__ == '__main__':
    main()
