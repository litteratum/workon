"""Script main module."""
import glob
import json
import logging
import os
import shutil
import subprocess

from . import git
from .errors import ScriptError


CONFIG_PATH = os.path.expanduser('~/.config/workon/config.json')


def _validate_config(config):
    if config.get('dir') and not isinstance(config['dir'], str):
        raise ScriptError(
            'Invalid config: "dir" parameter should be of string type')
    if config.get('editor') and not isinstance(config['editor'], str):
        raise ScriptError(
            'Invalid config: "editor" parameter should be of string type')
    if config.get('source') and not isinstance(config['source'], list):
        raise ScriptError(
            'Invalid config: "source" parameter should be of array type')

    return config


def get_config():
    """Return config loaded from `CONFIG_PATH`."""
    try:
        with open(CONFIG_PATH) as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        logging.warning('Failed to load user config file: %s. Skipping', exc)
        config = {}
    except OSError as exc:
        logging.warning(
            'Failed to load user configuration file: %s. Skipping', exc)
        config = {}

    return _validate_config(config)


def _remove_project(project, directory, force):
    logging.info('Finishing up "%s"', project)
    proj_path = os.path.join(directory, project)

    if not git.is_stash_empty(proj_path) and not force:
        raise ScriptError(
            'Wait a moment, you have left some stashes! If you are confident, '
            'use "-f" flag'
        )

    unpushed_info = git.get_unpushed_branches_info(proj_path)
    if unpushed_info and not force:
        raise ScriptError(
            'Wait a moment, you left some unpushed commits! Please, '
            'take a look:\n%s\n\nIf you are confident, use "-f" flag'
            % unpushed_info
        )

    unstaged_changes = git.get_unstaged_info(proj_path)
    if unstaged_changes and not force:
        raise ScriptError(
            'Wait a moment, you left some unstaged changes! Please, '
            'take a look:\n%s\n\nIf you are confident, use "-f" flag'
            % unstaged_changes
        )

    logging.debug('Removing "%s"', proj_path)
    shutil.rmtree(proj_path)


def done(args):
    """Finish up with a project(s)."""
    try:
        projects = os.listdir(args.directory)
    except OSError as exc:
        raise ScriptError(
            'Oops, can\'t access working directory: %s' % exc) from exc

    if args.project:
        if args.project not in projects:
            raise ScriptError(
                '"%s" not found in "%s"' % (args.project, args.directory))
        _remove_project(args.project, args.directory, args.force)
    else:
        for project in projects:
            if os.path.isdir(os.path.join(args.directory, project)):
                try:
                    _remove_project(project, args.directory, args.force)
                except ScriptError as exc:
                    logging.error(exc)
                    continue
        # there may be some files left
        for filepath in glob.glob(os.path.join(args.directory, '*')):
            if os.path.islink(filepath):
                os.unlink(filepath)
            elif not os.path.isdir(filepath):
                os.remove(filepath)


def start(args):
    """Start your work on a project.

    * clones the project from GIT
    * checks if working directory is empty
    """
    logging.info('Setting up "%s"', args.project)

    for i, source in enumerate(args.source, start=1):
        project_path = source.strip('/') + '/' + args.project + '.git'
        destination = args.directory + '/{}'.format(args.project)

        try:
            git.clone(project_path, destination)
            break
        except ScriptError as exc:
            if i == len(args.source):
                raise
            logging.warning('%s. Will try the next source', exc)

    if not args.noopen:
        _open_project(args)


def open_project(args):
    """Open the project in specified editor."""
    _open_project(args)


def _open_project(args):
    project_dir = os.path.join(args.directory, args.project)

    if not os.path.isdir(project_dir):
        raise ScriptError(
            'No project named "%s" found under your working directory'
            % args.project
        )

    for editor in (args.editor, os.environ.get('EDITOR'), 'vi', 'vim'):
        if editor:
            logging.info(
                'Trying to open "%s" with "%s" editor', args.project, editor)
            try:
                result = subprocess.run([editor, project_dir], check=False)
            except OSError as exc:
                logging.error(
                    'Failed to open "%s" with "%s": %s',
                    args.project, args.editor, exc
                )
            else:
                if result.returncode == 0:
                    break
    else:
        raise ScriptError('No suitable editor found to open your project')
