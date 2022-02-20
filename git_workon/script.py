"""Script main module."""
import glob
import json
import logging
import os
import shutil
import subprocess
from typing import Optional

import appdirs
import pkg_resources

from . import git

_CONFIG_DIR = appdirs.user_config_dir("git_workon")
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")


class ScriptError(Exception):
    """Error in script."""


def _validate_config(user_config):
    if user_config.get("dir") and not isinstance(user_config["dir"], str):
        raise ScriptError('Invalid config: "dir" parameter should be of string type')
    if user_config.get("editor") and not isinstance(user_config["editor"], str):
        raise ScriptError('Invalid config: "editor" parameter should be of string type')
    if user_config.get("source") and not isinstance(user_config["source"], list):
        raise ScriptError('Invalid config: "source" parameter should be of array type')

    return user_config


def get_config():
    """Return config loaded from `_CONFIG_PATH`."""
    try:
        with open(_CONFIG_PATH, encoding="utf8") as file:
            user_config = json.load(file)
    except json.JSONDecodeError as exc:
        logging.warning("Failed to load user config file: %s. Skipping", exc)
        user_config = {}
    except OSError as exc:
        logging.warning("Failed to load user configuration file: %s. Skipping", exc)
        user_config = {}

    return _validate_config(user_config)


def done(args):
    """Finish up with a project(s)."""
    try:
        projects = os.listdir(args.directory)
    except OSError as exc:
        raise ScriptError(f"Oops, can't access working directory: {exc}") from exc

    if args.project:
        if args.project not in projects:
            raise ScriptError(f'"{args.project}" not found in "{args.directory}"')
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
        for filepath in glob.glob(os.path.join(args.directory, "*")):
            if os.path.islink(filepath):
                logging.debug('Removing symlink "%s"', filepath)
                os.unlink(filepath)
            elif not os.path.isdir(filepath):
                logging.debug('Removing file "%s"', filepath)
                os.remove(filepath)


def _remove_project(project, directory, force):
    logging.info('Finishing up "%s"', project)
    proj_path = os.path.join(directory, project)

    if not git.is_git_dir(proj_path):
        logging.debug('Not a GIT repository, removing "%s"', proj_path)
        shutil.rmtree(proj_path)
        return

    try:
        if force or git.check_all_pushed(proj_path) is None:
            logging.debug('Removing "%s"', proj_path)
            shutil.rmtree(proj_path)
    except git.GITError as exc:
        raise ScriptError(
            f"Failed. There are some unpushed changes or problems! See below\n\n"
            f"{exc}\n"
            f'Push your local changes or use "-f" flag to drop them'
        ) from exc


def start(args):
    """Start your work on a project.

    Opens the project if it already cloned. Otherwise:
      * clones the project from GIT
      * checks if working directory is empty
    """
    if args.project in os.listdir(args.directory):
        logging.info("The project is already in the working directory")
        if args.noopen:
            logging.warning(
                "The command was executed for existing project with --noopen "
                "flag. Nothing to do."
            )
        else:
            _open_project(args.directory, args.project, args.editor)
        return

    for i, source in enumerate(args.source, start=1):
        project_path = source.strip("/") + "/" + args.project + ".git"
        destination = f'{args.directory}/{args.project}'

        try:
            git.clone(project_path, destination)
            break
        except git.GITError as exc:
            if i == len(args.source):
                raise ScriptError(
                    f'Failed to clone "{args.project}". Tried all configured sources'
                ) from exc
            logging.debug(exc)

    if not args.noopen:
        _open_project(args.directory, args.project, args.editor)


def _open_with_editor(editor: Optional[str], path: str):
    for editor_ in (editor, os.environ.get("EDITOR"), "vi", "vim"):
        if editor_:
            logging.info('Trying to open "%s" with "%s" editor', path, editor_)
            try:
                result = subprocess.run([editor_, path], check=False)
            except OSError as exc:
                logging.error('Failed to open "%s" with "%s": %s', path, editor_, exc)
            else:
                if result.returncode == 0:
                    break
    else:
        raise ScriptError(f'No suitable editor found to open "{path}"')


def _open_project(directory, project, editor):
    project_dir = os.path.join(directory, project)

    if not os.path.isdir(project_dir):
        raise ScriptError(
            f'No project named "{project}" found under your working directory'
        )

    _open_with_editor(editor, project_dir)


def config(args):
    """Handle `config` command.

    Create config directory and opens an editor to modify the config.
    """
    logging.debug('Creating config directory "%s"', _CONFIG_DIR)
    os.makedirs(_CONFIG_DIR, exist_ok=True)

    if not os.path.exists(_CONFIG_PATH):
        logging.debug('Copying config template to "%s"', _CONFIG_PATH)
        shutil.copy(
            pkg_resources.resource_filename("git_workon", "config.json"),
            _CONFIG_PATH,
        )

    _open_with_editor(args.editor, _CONFIG_PATH)
