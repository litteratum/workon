"""Script main module."""
import glob
import json
import logging
import os
import shutil
import subprocess

from . import git


CONFIG_PATH = os.path.expanduser('~/.config/workon/config.json')


class ScriptError(Exception):
    """Error in script."""


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

    stashes_info = git.get_stash_info(proj_path)
    if stashes_info and not force:
        raise ScriptError(
            'There are stashes left for "%s"! Please, take a look:'
            '\n%s\nIf you are confident, use "-f" flag'
            % (project, stashes_info)
        )

    unpushed_info = git.get_unpushed_branches_info(proj_path)
    if unpushed_info and not force:
        raise ScriptError(
            'There are unpushed commits left for "%s"! Please, '
            'take a look:\n%s\nIf you are confident, use "-f" flag'
            % (project, unpushed_info)
        )

    unstaged_changes = git.get_unstaged_info(proj_path)
    if unstaged_changes and not force:
        raise ScriptError(
            'There are unstaged changes left for "%s"! Please, '
            'take a look:\n%s\nIf you are confident, use "-f" flag'
            % (project, unstaged_changes)
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
                logging.debug('Removing symlink "%s"', filepath)
                os.unlink(filepath)
            elif not os.path.isdir(filepath):
                logging.debug('Removing file "%s"', filepath)
                os.remove(filepath)


def start(args):
    """Start your work on a project.

    Opens the project if it already cloned. Otherwise:
      * clones the project from GIT
      * checks if working directory is empty
    """
    if args.project in os.listdir(args.directory):
        logging.info('The project is already in the working directory')
        if args.noopen:
            logging.warning(
                'The command was executed for existing project with --noopen '
                'flag. Nothing to do.'
            )
        else:
            _open_project(args.directory, args.project, args.editor)
        return

    logging.info('Setting up "%s"', args.project)

    for i, source in enumerate(args.source, start=1):
        project_path = source.strip('/') + '/' + args.project + '.git'
        destination = args.directory + '/{}'.format(args.project)

        try:
            git.clone(project_path, destination)
            break
        except git.GITError as exc:
            if i == len(args.source):
                raise
            logging.warning('%s. Will try the next source', exc)

    if not args.noopen:
        _open_project(args.directory, args.project, args.editor)


def _open_project(directory, project, editor):
    project_dir = os.path.join(directory, project)

    if not os.path.isdir(project_dir):
        raise ScriptError(
            'No project named "%s" found under your working directory'
            % project
        )

    for editor in (editor, os.environ.get('EDITOR'), 'vi', 'vim'):
        if editor:
            logging.info(
                'Trying to open "%s" with "%s" editor', project, editor)
            try:
                result = subprocess.run([editor, project_dir], check=False)
            except OSError as exc:
                logging.error(
                    'Failed to open "%s" with "%s": %s', project, editor, exc
                )
            else:
                if result.returncode == 0:
                    break
    else:
        raise ScriptError('No suitable editor found to open "%s"', project)
