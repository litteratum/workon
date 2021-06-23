"""Module for interaction with GIT."""
import logging
import subprocess

from .errors import ScriptError


def get_stash_info(directory):
    """Return stash info under `directory`."""
    logging.info('Checking GIT stashes under "%s"', directory)
    return subprocess.run(
        'git stash list'.split(), cwd=directory,
        capture_output=True, text=True, check=False
    ).stdout


def get_unpushed_branches_info(directory) -> str:
    """Return information about unpushed branches.

    Format is: <commit> (<branch>) <commit_message>
    """
    logging.info('Checking for unpushed GIT commits under "%s"', directory)
    return subprocess.run(
        'git log --branches --not --remotes --decorate --oneline'.split(),
        cwd=directory, capture_output=True, text=True, check=False
    ).stdout


def get_unstaged_info(directory) -> str:
    """Return information about unstaged changes."""
    logging.info('Checking for unstaged changes under "%s"', directory)
    return subprocess.run(
        'git status --short'.split(),
        cwd=directory, capture_output=True, text=True, check=False
    ).stdout


def clone(source, destination):
    """Clone a project from GIT `source` to `destination` directory."""
    try:
        logging.info('Cloning "%s" to "%s"', source, destination)
        subprocess.run(
            ['git', 'clone', source, destination],
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as exc:
        raise ScriptError(
            'Failed to clone "%s":\n%s' % (source, exc.stderr)) from exc
