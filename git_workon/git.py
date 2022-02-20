"""Module for interaction with GIT."""
import logging
import subprocess


class GITError(Exception):
    """Any error related with GIT usage."""


def _run_command(
    command: str, check=False, cwd: str = None
) -> subprocess.CompletedProcess:
    """Run command in subprocess."""
    logging.debug('Running command "%s"', command)
    return subprocess.run(
        command.split(), cwd=cwd, capture_output=True, text=True, check=check
    )


def get_stash_info(directory: str):
    """Return stash info under `directory`."""
    logging.info('Checking GIT stashes under "%s"', directory)
    return _run_command("git stash list", cwd=directory).stdout


def get_unpushed_branches_info(directory: str) -> str:
    """Return information about unpushed branches.

    Format is: <commit> (<branch>) <commit_message>
    """
    logging.info('Checking for unpushed GIT commits under "%s"', directory)
    return _run_command(
        "git log --branches --not --remotes --decorate --oneline", cwd=directory
    ).stdout


def get_unstaged_info(directory: str) -> str:
    """Return information about unstaged changes."""
    logging.info('Checking for unstaged changes under "%s"', directory)
    return _run_command("git status --short", cwd=directory).stdout


def get_unpushed_tags(directory: str) -> str:
    """Return unpushed tags.

    If no tags found, returns an empty string.
    If failed to get tags information, returns a string containing error
    description.
    """
    logging.info('Checking for unpushed tags under "%s"', directory)

    try:
        info = _run_command(
            "git push --tags --dry-run", cwd=directory, check=True
        ).stderr
    except subprocess.CalledProcessError as exc:
        return f"Failed to check unpushed tags: {exc.stderr}"

    if "new tag" not in info:
        return ""
    return info


def clone(source: str, destination: str):
    """Clone a project from GIT `source` to `destination` directory."""
    try:
        logging.info('Cloning "%s" to "%s"', source, destination)
        _run_command(f"git clone {source} {destination}", check=True)
    except subprocess.CalledProcessError as exc:
        raise GITError(f'Failed to clone "{source}":\n{exc.stderr}') from exc
