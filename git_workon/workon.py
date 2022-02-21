"""Module implementing GIT workon main logic."""
import glob
import logging
import os
import shutil
import subprocess
from typing import List

from . import git


class CommandError(Exception):
    """Command error."""


class WorkOnDir:
    """Wrapper around workon directory."""

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
                git.clone(
                    os.path.join(source.strip("/"), f"{project_name}.git"),
                    f"{self.directory}/{project_name}",
                )
                break
            except git.GITError as exc:
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

        if not git.is_git_dir(proj_path):
            logging.debug('Not a GIT repository, removing "%s"', proj_path)
            shutil.rmtree(proj_path)
            return

        try:
            if force or git.check_all_pushed(proj_path) is None:
                logging.debug('Removing "%s"', proj_path)
                shutil.rmtree(proj_path)
        except git.GITError as exc:
            raise CommandError(
                f"There are some unpushed changes or problems! See below\n\n"
                f"{exc}\n"
                f'Push your local changes or use "-f" flag to drop them'
            ) from exc

    def __contains__(self, item) -> bool:
        return item in self._dirs
