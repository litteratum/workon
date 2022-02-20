"""Tests for git.py."""
# pylint:disable=missing-function-docstring
import os
import re
import shutil
import subprocess
import tempfile
from typing import Iterable
from unittest.mock import Mock, patch

import pytest
from git_workon import git


class TmpGitDir:
    """Temporary GIT directory."""

    def __init__(self, initial_commit=False) -> None:
        self.path = tempfile.mkdtemp()
        self.initial_commit = initial_commit

        self._git_init()

    def _git_init(self):
        subprocess.run(["git", "init"], cwd=self.path, check=True)

        if self.initial_commit:
            os.mknod(os.path.join(self.path, "some"))
            self.add()
            self.commit()

    def add(self, files: Iterable[str] = None):
        if not files:
            subprocess.run(["git", "add", "--all"], cwd=self.path, check=True)
        else:
            for file in files:
                subprocess.run(["git", "add", file], cwd=self.path, check=True)

    def stash(self, include_untracked=True):
        command = ["git", "stash"]
        if include_untracked:
            command.append("--include-untracked")

        subprocess.run(command, cwd=self.path, check=True)

    def checkout(self, branch, create=True):
        command = ["git", "checkout", "-b" if create else "", branch]
        subprocess.run(command, cwd=self.path, check=True)

    def commit(self, message="dummy"):
        subprocess.run(["git", "commit", "-m", message], cwd=self.path, check=True)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        shutil.rmtree(self.path)


def test_is_git_dir():
    with TmpGitDir() as git_dir:
        assert git.is_git_dir(git_dir.path)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        assert not git.is_git_dir(tmp_dir_path)


def test_check_all_pushed_everything_is_pushed_returns_none():
    """If everything is pushed, the function should return None."""
    with TmpGitDir() as git_repo:
        with patch("git_workon.git.subprocess.run") as mc_run:
            mc_run.return_value = Mock(stderr="Everything up-to-date", stdout="")
            assert git.check_all_pushed(git_repo.path) is None


def test_check_all_pushed_there_is_some_stash_raises_exception():
    """If everything is pushed, the function should return None."""
    with TmpGitDir(initial_commit=True) as git_dir:
        os.mknod(os.path.join(git_dir.path, "1.txt"))
        git_dir.stash()
        pattern = r"stash@\{0\}: WIP on master: .+? dummy"

        with pytest.raises(git.GITError) as exc:
            git.check_all_pushed(git_dir.path)
        assert re.search(pattern, str(exc.value))


def test_check_all_pushed_branch_raises_exception():
    with TmpGitDir(initial_commit=True) as git_dir:
        git_dir.checkout("test")
        os.mknod(os.path.join(git_dir.path, "1.txt"))
        git_dir.add()
        git_dir.commit("example")

        with pytest.raises(git.GITError) as exc:
            git.check_all_pushed(git_dir.path)
        assert "(master) dummy" in str(exc.value)
        assert "(HEAD -> test) example" in str(exc.value)


def test_check_all_pushed_with_unstaged_returns_info():
    with TmpGitDir(initial_commit=True) as git_dir:
        git_dir.checkout("test")
        os.mknod(os.path.join(git_dir.path, "1.txt"))

        with pytest.raises(git.GITError) as exc:
            git.check_all_pushed(git_dir.path)
        assert "?? 1.txt\n" in str(exc.value)


def test_check_all_pushed_tags_no_remote_raises_exception():
    with TmpGitDir() as git_dir:
        with pytest.raises(git.GITError) as exc:
            git.check_all_pushed(git_dir.path)
        assert "Failed to check unpushed tags" in str(exc.value)


def test_check_all_pushed_tags_with_unpushed_raises_exception():
    with TmpGitDir(initial_commit=True) as git_dir:
        with patch("git_workon.git.subprocess.run") as mc_run:
            mc_run.return_value = Mock(
                stderr="* [new tag]         1.1.0 -> 1.1.0", stdout=""
            )
            with pytest.raises(git.GITError) as exc:
                git.check_all_pushed(git_dir.path)
            assert "1.1.0 -> 1.1.0" in str(exc.value)


def test_check_all_all_entities_are_unpushed_raises_exception():
    with TmpGitDir(initial_commit=True) as git_dir:
        with patch("git_workon.git.subprocess.run") as mc_run:
            mc_run.side_effect = [
                Mock(stdout="?? 1.txt\n"),
                Mock(stdout="stash{0}"),
                Mock(stdout="(master) dummy\n(HEAD -> test) example"),
                Mock(stderr="* [new tag]         1.1.0 -> 1.1.0", stdout=""),
            ]
            with pytest.raises(git.GITError) as exc:
                git.check_all_pushed(git_dir.path)
            for entity in "Stashes", "Commits", "Not staged", "Tags":
                assert entity in str(exc.value)


@patch("git_workon.git.subprocess.run")
def test_clone(mc_subprocess_run):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        mc_subprocess_run.side_effect = lambda *args, **kwargs: os.mkdir(
            os.path.join(tmp_dir_path, "a")
        )
        git.clone("http://localhost:3000/gogs/a", tmp_dir_path)
        assert os.path.exists(os.path.join(tmp_dir_path, "a"))


@patch("git_workon.git.subprocess.run")
def test_clone_no_such_project(mc_subprocess_run):
    mc_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, [], "", "not found"
    )
    with tempfile.TemporaryDirectory() as tmp_dir_path:

        with pytest.raises(git.GITError) as exc:
            git.clone("http://localhost:3000/gogs/c", tmp_dir_path)
        assert "not found" in str(exc.value)


@patch("git_workon.git.subprocess.run")
def test_clone_already_exists(mc_subprocess_run):
    mc_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, [], "", "already exists"
    )
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        directory = os.path.join(tmp_dir_path, "a")
        os.mkdir(directory)
        os.mknod(os.path.join(directory, "some"))

        with pytest.raises(git.GITError) as exc:
            git.clone("http://localhost:3000/gogs/a", tmp_dir_path)
        assert "already exists" in str(exc.value)
