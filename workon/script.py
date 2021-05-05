"""Script main module."""
import logging
import os
import shutil

from . import git
from .errors import ScriptError


def _remove_project(project, directory, force):
    logging.info('Finishing up "%s"', project)
    proj_path = os.path.join(directory, project)

    if not git.is_stash_empty(proj_path) and not force:
        raise ScriptError(
            'Wait a moment, you left some stashes! If you don\'t '
            'care, use "-f" flag'
        )

    unpushed_info = git.get_unpushed_branches_info(proj_path)
    if unpushed_info and not force:
        raise ScriptError(
            'Wait a moment, you left some unpushed commits! Please, '
            'take a look:\n%s\n\nIf you don\'t care, use "-f" flag'
            % unpushed_info
        )

    logging.debug('Removing "%s"', proj_path)
    shutil.rmtree(proj_path)


def done(args):
    """Finish up with a project(s)."""
    try:
        projects = os.listdir(args.directory)
    except OSError as exc:
        raise ScriptError(
            'Oops, can\'t access specified directory: %s' % exc) from exc

    if args.project:
        if args.project not in projects:
            raise ScriptError(
                '"%s" not found in "%s"' % (args.project, args.directory))
        _remove_project(args.project, args.directory, args.force)
    else:
        for project in projects:
            _remove_project(project, args.directory, args.force)


def start(args):
    """Start your work on a project.

    * clones the project from GIT
    * checks is working directory is empty
    """
    logging.info('Setting up "%s"', args.project)

    if len(os.listdir(args.directory)) > 0 and not args.force:
        raise ScriptError(
            'Your working directory is not empty. It is encouraged that you '
            'start with a clean desk.\nUse -f/--force flag if you insist on it'
        )

    project_path = args.source.strip('/') + '/' + args.project + '.git'
    destination = args.directory + '/{}'.format(args.project)
    git.clone(project_path, destination)
