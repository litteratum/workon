"""Module for interaction with GIT."""
import glob
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, List, Optional


class GITError(Exception):
    """Any error related with GIT usage."""


class CommandError(Exception):
    """Command error."""


class ProjectStatus(Enum):
    """GIT project status."""

    CLEAN = "clean"
    DIRTY = "dirty"
    UNDEFINED = "undefined"


@dataclass
class ProjectInfo:
    """GIT Project information."""

    name: str
    status: Optional[ProjectStatus]


def _run_command(
    command: str, check=False, cwd: str = None
) -> subprocess.CompletedProcess:
    """Run command in subprocess."""
    logging.debug('Running command "%s"', command)
    return subprocess.run(
        command.split(), cwd=cwd, capture_output=True, text=True, check=check
    )


def is_git_dir(directory: str) -> bool:
    """Return whether a directory is GIT initialized directory."""
    return os.path.isdir(directory) and ".git" in os.listdir(directory)


def _get_stash_info(directory: str):
    """Return stash info under `directory`."""
    logging.debug('Checking for unpushed GIT stashes under "%s"', directory)
    return _run_command("git stash list", cwd=directory).stdout


def _get_unpushed_branches_info(directory: str) -> str:
    """Return information about unpushed branches.

    Format is: <commit> (<branch>) <commit_message>
    """
    logging.debug('Checking for unpushed GIT commits under "%s"', directory)
    return _run_command(
        "git log --branches --not --remotes --decorate --oneline", cwd=directory
    ).stdout


def _get_unstaged_info(directory: str) -> str:
    """Return information about unstaged changes."""
    logging.debug('Checking for unstaged changes under "%s"', directory)
    return _run_command("git status --short", cwd=directory).stdout


def _get_unpushed_tags(directory: str) -> str:
    """Return unpushed tags.

    If no tags found, returns an empty string.
    If failed to get tags information, returns a string containing error
    description.
    """
    logging.debug('Checking for unpushed tags under "%s"', directory)

    try:
        info = _run_command(
            "git push --tags --dry-run", cwd=directory, check=True
        ).stderr
    except subprocess.CalledProcessError as exc:
        return f"Failed to check unpushed tags: {exc.stderr}"

    if "new tag" not in info:
        return ""
    return info


def check_all_pushed(directory: str) -> None:
    """Check if everything from GIT directory is pushed.

    It checks:
      * stashes
      * branches
      * unstaged
      * tags

    :raises: `GITError` if there is something unpushed. Error message contains
      information about unpushed entities
    """
    unstaged = _get_unstaged_info(directory)
    stashes = _get_stash_info(directory)
    branches = _get_unpushed_branches_info(directory)
    tags = _get_unpushed_tags(directory)

    if any([unstaged, stashes, branches, tags]):
        output = ""
        if stashes:
            output += f"Stashes:\n{stashes}"
        if branches:
            output += f"\nCommits:\n{branches}"
        if unstaged:
            output += f"\nNot staged:\n{unstaged}"
        if tags:
            output += f"\nTags:\n{tags}"

        raise GITError(output)


def clone(source: str, destination: str):
    """Clone a project from GIT `source` to `destination` directory."""
    try:
        logging.info('Cloning "%s" to "%s"', source, destination)
        _run_command(f"git clone {source} {destination}", check=True)
    except subprocess.CalledProcessError as exc:
        raise GITError(f'Failed to clone "{source}":\n{exc.stderr}') from exc


class WorkingDir:
    """Encapsulates working directory for GIT projects."""

    def __init__(self, directory: str) -> None:
        self.directory = os.path.expanduser(directory)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        os.makedirs(self.directory, exist_ok=True)

    @property
    def _dirs(self) -> List[str]:
        return os.listdir(self.directory)

    def remove(self, project_name: str = None, force: bool = False) -> None:
        """Remove project from the directory.

        If `project_name` is not specified, all projects will be removed.
        """
        if project_name:
            if project_name not in self._dirs:
                raise CommandError(f'"{project_name}" not found in "{self.directory}"')
            self._remove_project(project_name, force)
        else:
            self._remove_projects(force)

    def clone(self, project_name: str, sources: List[str]) -> None:
        """Clone a project to the working directory."""
        if project_name in self._dirs:
            raise CommandError(f'Project "{project_name}" is already cloned')

        for i, source in enumerate(sources, start=1):
            try:
                clone(
                    os.path.join(source.strip("/"), f"{project_name}.git"),
                    f"{self.directory}/{project_name}",
                )
                break
            except GITError as exc:
                if i == len(sources):
                    raise CommandError(
                        f'Failed to clone "{project_name}". Tried all configured sources'
                    ) from exc
                logging.debug(exc)

    def open(self, project_name: str, editor: str = None) -> None:
        """Open a project from the directory.

        If editor is not specified, try $EDITOR, vi, vim consequently.
        """
        project_dir = os.path.join(self.directory, project_name)

        if not os.path.isdir(project_dir):
            raise CommandError(
                f'No project named "{project_name}" found under the working directory'
            )

        for editor_ in (editor, os.environ.get("EDITOR"), "vi", "vim"):
            if editor_:
                logging.info('Opening "%s" with "%s" editor', project_dir, editor_)
                result = subprocess.run([editor_, project_dir], check=False)
                if result.returncode == 0:
                    break
        else:
            raise CommandError(f'No suitable editor found to open "{project_dir}"')

    def show(self, check_status: bool) -> Iterator[ProjectInfo]:
        """Return information about GIT projects."""
        for project in self._dirs:
            yield ProjectInfo(
                project, self._get_project_status(project) if check_status else None
            )

    def _get_project_status(self, project_name: str) -> ProjectStatus:
        path = os.path.join(self.directory, project_name)
        if not is_git_dir(path):
            return ProjectStatus.UNDEFINED
        try:
            check_all_pushed(path)
        except GITError:
            return ProjectStatus.DIRTY
        else:
            return ProjectStatus.CLEAN

    def _remove_projects(self, force: bool = False) -> None:
        for project in self._dirs:
            if os.path.isdir(os.path.join(self.directory, project)):
                try:
                    self._remove_project(project, force=force)
                except CommandError as exc:
                    logging.error(exc)
                    continue
        # there may be some files left
        for filepath in glob.glob(os.path.join(self.directory, "*")):
            if os.path.islink(filepath):
                logging.debug('Removing symlink "%s"', filepath)
                os.unlink(filepath)
            elif not os.path.isdir(filepath):
                logging.debug('Removing file "%s"', filepath)
                os.remove(filepath)

    def _remove_project(self, project_name: str, force: bool = False) -> None:
        logging.info('Finishing up "%s"', project_name)
        proj_path = os.path.join(self.directory, project_name)

        if not is_git_dir(proj_path):
            logging.debug('Not a GIT repository, removing "%s"', proj_path)
            shutil.rmtree(proj_path)
            return

        try:
            if force or check_all_pushed(proj_path) is None:
                logging.debug('Removing "%s"', proj_path)
                shutil.rmtree(proj_path)
        except GITError as exc:
            raise CommandError(
                f"There are some unpushed changes or problems! See below\n\n"
                f"{exc}\n"
                f'Push your local changes or use "-f" flag to drop them'
            ) from exc

    def __contains__(self, item) -> bool:
        return item in self._dirs
