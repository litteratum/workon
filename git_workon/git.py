"""Module for interaction with GIT."""
import logging
import subprocess


class GITError(Exception):
    """Any error related with GIT usage."""


def get_stash_info(directory: str):
    """Return stash info under `directory`."""
    logging.debug('Checking GIT stashes under "%s"', directory)
    return subprocess.run(
        'git stash list'.split(), cwd=directory,
        capture_output=True, text=True, check=False
    ).stdout


def get_unpushed_branches_info(directory: str) -> str:
    """Return information about unpushed branches.

    Format is: <commit> (<branch>) <commit_message>
    """
    logging.debug('Checking for unpushed GIT commits under "%s"', directory)
    return subprocess.run(
        'git log --branches --not --remotes --decorate --oneline'.split(),
        cwd=directory, capture_output=True, text=True, check=False
    ).stdout


def get_unstaged_info(directory: str) -> str:
    """Return information about unstaged changes."""
    logging.debug('Checking for unstaged changes under "%s"', directory)
    return subprocess.run(
        'git status --short'.split(),
        cwd=directory, capture_output=True, text=True, check=False
    ).stdout


def get_unpushed_tags(directory: str) -> str:
    """Return unpushed tags.

    If no tags found, returns an empty string.
    If failed to get tags information, returns a string containing error
    description.
    """
    logging.debug('Checking for unpushed tags under "%s"', directory)

    try:
        info = subprocess.run(
            'git push --tags --dry-run'.split(),
            cwd=directory, capture_output=True, text=True, check=True
        ).stderr
    except subprocess.CalledProcessError as exc:
        return 'Failed to check unpushed tags: {}'.format(exc.stderr)

    if 'new tag' not in info:
        return ''
    return info


def clone(source: str, destination: str):
    """Clone a project from GIT `source` to `destination` directory."""
    try:
        logging.debug('Cloning "%s" to "%s"', source, destination)
        subprocess.run(
            ['git', 'clone', source, destination],
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as exc:
        raise GITError(
            'Failed to clone "%s":\n%s' % (source, exc.stderr)) from exc
